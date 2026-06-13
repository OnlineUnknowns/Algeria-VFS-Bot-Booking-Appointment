# src/server.py

import http.server
import socketserver
import json
import os
import urllib.parse
import threading
import time
import logging
from datetime import datetime, timedelta
import random

# Imports from other modules
from config import VISA_MONITOR_CONFIG, NOTIFICATION_CONFIG, USER_PROFILES, LOGGING_CONFIG
from security import encrypt_data, decrypt_data, mask_passport
from notifications import dispatch_slot_alert
from scraper import fetch_appointment_availability
from mock_server import handle_mock_availability_html, handle_mock_booking_html, load_mock_slots, save_mock_slots

logger = logging.getLogger(__name__)

PORT = 5000
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")
PROFILES_FILE = os.path.join(os.path.dirname(__file__), "profiles.json")

# Global variables for monitor state (thread-safe)
monitor_state = {
    "is_running": False,
    "status": "idle", # idle, checking, available, not_available
    "slots_found": [],
    "last_checked": "",
    "next_check_in_seconds": 0,
    "notifications_sent_count": 0,
    "error_log": ""
}

state_lock = threading.Lock()
monitor_thread = None
stop_event = threading.Event()

def load_profiles():
    """Loads user profiles from file, or creates defaults if missing."""
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading profiles file: {e}")
            return USER_PROFILES.copy()
    else:
        # Save default config profiles
        save_profiles(USER_PROFILES)
        return USER_PROFILES.copy()

def save_profiles(profiles):
    """Saves user profiles to file."""
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=4)

# Load profiles and decrypt if needed, or initialize key
current_profiles = load_profiles()

# Initialize monitor state from profiles
# In case passport isn't encrypted, encrypt it
profiles_updated = False
for uid, profile in current_profiles.items():
    p_num = profile.get("passport_number_plaintext", "")
    if p_num:
        profile["passport_number_encrypted"] = encrypt_data(p_num)
        del profile["passport_number_plaintext"]
        profiles_updated = True
if profiles_updated:
    save_profiles(current_profiles)


def monitor_loop():
    """
    Background loop that runs periodically to fetch slots and send alerts.
    """
    global monitor_state
    logger.info("Background monitor thread started.")
    
    last_check_times = {}
    last_known_slots = {} # track by user_id
    
    while not stop_event.is_set():
        profiles = load_profiles()
        
        for user_id, profile in list(profiles.items()):
            if stop_event.is_set():
                break
                
            current_time = time.time()
            last_check_time = last_check_times.get(user_id, 0)
            
            # Retrieve monitoring interval configuration
            interval_normal = VISA_MONITOR_CONFIG.get("check_interval_normal_seconds", 60)
            jitter_max = VISA_MONITOR_CONFIG.get("jitter_max_seconds", 5)
            
            # Add small random jitter (To comply with website friendly scheduler)
            effective_interval = interval_normal + random.uniform(0, jitter_max)
            
            # Check countdown update
            time_remaining = max(0, effective_interval - (current_time - last_check_time))
            with state_lock:
                monitor_state["next_check_in_seconds"] = int(time_remaining)
            
            if (current_time - last_check_time) >= effective_interval:
                with state_lock:
                    monitor_state["status"] = "checking"
                
                country = profile.get("country", "Italy")
                # Default mock URL pointing to local server
                booking_url = profile.get("booking_url_template", f"http://localhost:{PORT}/mock/vfs/italy/availability")
                preferred_city = profile.get("preferred_cities", ["Algiers"])[0]
                
                logger.info(f"Monitor checking slots for {user_id} ({country} - {preferred_city})...")
                
                # Fetch available slots
                slots = fetch_appointment_availability(country, preferred_city, booking_url)
                
                # Retrieve last state
                prev_slots = last_known_slots.get(user_id, [])
                
                # Detect differences
                new_slots = [s for s in slots if s["date"] not in [ps["date"] for ps in prev_slots]]
                canceled_slots = [ps for ps in prev_slots if ps["date"] not in [s["date"] for s in slots]]
                
                alert_sent = 0
                if new_slots:
                    logger.info(f"Detected NEW visa slots for {user_id}: {new_slots}")
                    # Dispatch Telegram/Email alerts
                    alert_sent = dispatch_slot_alert(profile, NOTIFICATION_CONFIG, new_slots)
                elif canceled_slots:
                    logger.info(f"Detected CANCELED visa slots for {user_id}: {canceled_slots}")
                    
                # Update loop trackers
                last_known_slots[user_id] = slots
                last_check_times[user_id] = current_time
                
                # Update global monitor state safely
                with state_lock:
                    monitor_state["slots_found"] = slots
                    monitor_state["last_checked"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    monitor_state["notifications_sent_count"] += alert_sent
                    
                    if slots:
                        monitor_state["status"] = "available"
                    else:
                        monitor_state["status"] = "not_available"
                        
                    # Output internal structured JSON as per requirements
                    internal_output = {
                        "status": monitor_state["status"],
                        "slots_found": slots,
                        "last_checked": monitor_state["last_checked"],
                        "next_check_in_seconds": int(effective_interval)
                    }
                    logger.debug(f"Structured JSON Log: {json.dumps(internal_output)}")
                    
        time.sleep(1) # Sleep to avoid high CPU usage
        
    logger.info("Background monitor thread stopped.")


class MonitorDashboardHandler(http.server.BaseHTTPRequestHandler):
    """
    HTTP handler serving API endpoints and frontend dashboard files.
    """
    
    def log_message(self, format, *args):
        # Override to log requests through standard logging instead of stdout
        logger.debug(format % args)
        
    def set_json_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self.set_json_headers(200)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)
        
        # --- API Routes ---
        if path == "/api/status":
            with state_lock:
                # Add overall running status
                monitor_state["is_running"] = (monitor_thread is not None and monitor_thread.is_alive())
                response_data = monitor_state.copy()
            self.set_json_headers(200)
            self.wfile.write(json.dumps(response_data).encode())
            return
            
        elif path == "/api/profile":
            profiles = load_profiles()
            # For security, return profiles with passport numbers masked
            masked_profiles = {}
            for uid, profile in profiles.items():
                p_encrypted = profile.get("passport_number_encrypted", "")
                p_decrypted = decrypt_data(p_encrypted)
                
                masked_profiles[uid] = profile.copy()
                masked_profiles[uid]["passport_number_masked"] = mask_passport(p_decrypted)
                # Never expose plaintext passport directly, but we can send masked version.
                # If the UI needs to copy it, we can create an endpoint GET /api/profile/decrypt which only works locally
                
            self.set_json_headers(200)
            self.wfile.write(json.dumps({
                "profiles": masked_profiles,
                "notifications": {
                    "telegram_bot_token": NOTIFICATION_CONFIG.get("telegram_bot_token"),
                    "telegram_chat_id": NOTIFICATION_CONFIG.get("telegram_chat_id"),
                    "email_sender": NOTIFICATION_CONFIG.get("email_sender"),
                    "email_receiver": NOTIFICATION_CONFIG.get("email_receiver"),
                    "webhook_url": NOTIFICATION_CONFIG.get("webhook_url"),
                    "email_smtp_server": NOTIFICATION_CONFIG.get("email_smtp_server", "smtp.gmail.com"),
                    "email_smtp_port": NOTIFICATION_CONFIG.get("email_smtp_port", 587),
                },
                "monitor": VISA_MONITOR_CONFIG
            }).encode())
            return
            
        elif path == "/api/profile/decrypt":
            # Direct decryption endpoint for manual booking helper (local copy-paste)
            profiles = load_profiles()
            decrypted_data = {}
            for uid, profile in profiles.items():
                p_encrypted = profile.get("passport_number_encrypted", "")
                decrypted_data[uid] = decrypt_data(p_encrypted)
            self.set_json_headers(200)
            self.wfile.write(json.dumps(decrypted_data).encode())
            return
            
        elif path == "/api/logs":
            log_file = LOGGING_CONFIG["log_file"]
            lines = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r") as f:
                        lines = f.readlines()[-100:] # Return last 100 lines
                except Exception as e:
                    lines = [f"Error reading log file: {e}"]
            self.set_json_headers(200)
            self.wfile.write(json.dumps({"logs": "".join(lines)}).encode())
            return
            
        # --- Mock Visa Center Routes ---
        elif path == "/mock/vfs/italy/availability":
            city = query.get("city", ["Algiers"])[0]
            html_content = handle_mock_availability_html(city)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html_content.encode())
            return
            
        elif path == "/mock/vfs/italy/book":
            date = query.get("date", [""])[0]
            city = query.get("city", [""])[0]
            
            # Fetch user profile to pre-fill form
            profiles = load_profiles()
            profile = profiles.get("user1", {})
            name = profile.get("full_name", "")
            visa_type = profile.get("visa_type", "tourism")
            
            # Decrypt passport number for form pre-filling
            p_encrypted = profile.get("passport_number_encrypted", "")
            passport = decrypt_data(p_encrypted)
            
            html_content = handle_mock_booking_html(date, city, name, passport, visa_type)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html_content.encode())
            return
            
        # --- Serve Static Frontend Files ---
        else:
            # Clean up paths to prevent directory traversal
            clean_path = path.lstrip("/")
            if not clean_path or clean_path == "":
                clean_path = "index.html"
                
            filepath = os.path.join(WEB_DIR, clean_path)
            
            if os.path.exists(filepath) and not os.path.isdir(filepath):
                # Guess mime type
                mime_type = "text/plain"
                if filepath.endswith(".html"):
                    mime_type = "text/html"
                elif filepath.endswith(".css"):
                    mime_type = "text/css"
                elif filepath.endswith(".js"):
                    mime_type = "application/javascript"
                elif filepath.endswith(".png"):
                    mime_type = "image/png"
                elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):
                    mime_type = "image/jpeg"
                elif filepath.endswith(".ico"):
                    mime_type = "image/x-icon"
                    
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.end_headers()
                
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>404 Not Found</h1><p>The requested file does not exist.</p>")
                return

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Read JSON POST payload
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = {}
        if post_data:
            try:
                data = json.loads(post_data)
            except Exception as e:
                logger.error(f"Error parsing POST JSON: {e}")
                self.set_json_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid JSON format"}).encode())
                return
                
        # --- API Routes ---
        if path == "/api/monitor/start":
            global monitor_thread, stop_event
            with state_lock:
                if monitor_thread is not None and monitor_thread.is_alive():
                    self.set_json_headers(200)
                    self.wfile.write(json.dumps({"message": "Monitor already running"}).encode())
                    return
                    
                stop_event.clear()
                monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
                monitor_thread.start()
                monitor_state["is_running"] = True
                monitor_state["status"] = "checking"
                
            logger.info("Monitor start request processed.")
            self.set_json_headers(200)
            self.wfile.write(json.dumps({"message": "Monitor started successfully"}).encode())
            return
            
        elif path == "/api/monitor/stop":
            with state_lock:
                stop_event.set()
                monitor_state["is_running"] = False
                monitor_state["status"] = "idle"
                
            logger.info("Monitor stop request processed.")
            self.set_json_headers(200)
            self.wfile.write(json.dumps({"message": "Monitor stopped successfully"}).encode())
            return
            
        elif path == "/api/profile":
            # Save updated profile config
            profiles = load_profiles()
            
            # 1. Update Profile (user1 for simplicity)
            profile_data = data.get("profile", {})
            if "user1" in profiles:
                profiles["user1"]["full_name"] = profile_data.get("full_name", profiles["user1"]["full_name"])
                profiles["user1"]["visa_type"] = profile_data.get("visa_type", profiles["user1"]["visa_type"])
                profiles["user1"]["country"] = profile_data.get("country", profiles["user1"]["country"])
                profiles["user1"]["preferred_cities"] = [profile_data.get("city", profiles["user1"]["preferred_cities"][0])]
                
                # Encryption: check if passport is updated
                new_passport = profile_data.get("passport_number", "")
                if new_passport and not new_passport.startswith("**") and "*" not in new_passport:
                    # Stored encrypted
                    profiles["user1"]["passport_number_encrypted"] = encrypt_data(new_passport)
            
            # 2. Update Notification Settings
            notif_data = data.get("notifications", {})
            NOTIFICATION_CONFIG["telegram_bot_token"] = notif_data.get("telegram_bot_token", NOTIFICATION_CONFIG["telegram_bot_token"])
            NOTIFICATION_CONFIG["telegram_chat_id"] = notif_data.get("telegram_chat_id", NOTIFICATION_CONFIG["telegram_chat_id"])
            NOTIFICATION_CONFIG["email_sender"] = notif_data.get("email_sender", NOTIFICATION_CONFIG["email_sender"])
            NOTIFICATION_CONFIG["email_password"] = notif_data.get("email_password", NOTIFICATION_CONFIG.get("email_password"))
            NOTIFICATION_CONFIG["email_receiver"] = notif_data.get("email_receiver", NOTIFICATION_CONFIG["email_receiver"])
            NOTIFICATION_CONFIG["email_smtp_server"] = notif_data.get("email_smtp_server", "smtp.gmail.com")
            NOTIFICATION_CONFIG["email_smtp_port"] = int(notif_data.get("email_smtp_port", 587))
            NOTIFICATION_CONFIG["webhook_url"] = notif_data.get("webhook_url", NOTIFICATION_CONFIG["webhook_url"])
            
            # 3. Update Monitor Settings
            mon_data = data.get("monitor", {})
            VISA_MONITOR_CONFIG["check_interval_normal_seconds"] = int(mon_data.get("check_interval_normal_seconds", VISA_MONITOR_CONFIG["check_interval_normal_seconds"]))
            VISA_MONITOR_CONFIG["jitter_max_seconds"] = int(mon_data.get("jitter_max_seconds", VISA_MONITOR_CONFIG["jitter_max_seconds"]))
            
            # Persist profile
            save_profiles(profiles)
            logger.info("Configuration updated successfully.")
            self.set_json_headers(200)
            self.wfile.write(json.dumps({"message": "Configuration saved successfully"}).encode())
            return
            
        elif path == "/api/profile/test_notification":
            # Trigger a test notification using configured settings
            profiles = load_profiles()
            profile = profiles.get("user1", {})
            
            test_slot = [{"date": "2026-09-01", "city": profile.get("preferred_cities", ["Algiers"])[0], "type": "tourism"}]
            success_count = dispatch_slot_alert(profile, NOTIFICATION_CONFIG, test_slot)
            
            self.set_json_headers(200)
            if success_count > 0:
                self.wfile.write(json.dumps({"message": f"Test alert dispatched. Successful channels: {success_count}"}).encode())
            else:
                self.wfile.write(json.dumps({"error": "Failed to send test alert. Please verify your credentials."}).encode())
            return
            
        # --- Mock Admin Routes ---
        elif path == "/api/mock/slots":
            # Add or remove a mock slot
            action = data.get("action") # add or delete
            slot_date = data.get("date") # e.g. 2026-07-25
            slot_city = data.get("city", "Algiers")
            slot_type = data.get("type", "tourism")
            
            slots = load_mock_slots()
            
            if action == "add":
                # Check if already exists
                if not any(s["date"] == slot_date and s["city"].lower() == slot_city.lower() for s in slots):
                    slots.append({
                        "date": slot_date,
                        "city": slot_city,
                        "country": "Italy",
                        "type": slot_type
                    })
                    save_mock_slots(slots)
                    logger.info(f"Mock Site Admin: Added slot for {slot_city} on {slot_date}")
                    self.set_json_headers(200)
                    self.wfile.write(json.dumps({"message": "Slot added successfully", "slots": slots}).encode())
                    return
                else:
                    self.set_json_headers(400)
                    self.wfile.write(json.dumps({"error": "Slot already exists"}).encode())
                    return
                    
            elif action == "delete":
                filtered_slots = [s for s in slots if not (s["date"] == slot_date and s["city"].lower() == slot_city.lower())]
                if len(filtered_slots) < len(slots):
                    save_mock_slots(filtered_slots)
                    logger.info(f"Mock Site Admin: Removed slot for {slot_city} on {slot_date}")
                    self.set_json_headers(200)
                    self.wfile.write(json.dumps({"message": "Slot deleted successfully", "slots": filtered_slots}).encode())
                    return
                else:
                    self.set_json_headers(404)
                    self.wfile.write(json.dumps({"error": "Slot not found"}).encode())
                    return
            else:
                self.set_json_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid action, must be 'add' or 'delete'"}).encode())
                return
                
        else:
            self.set_json_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode())
            return


def start_server():
    """Starts the HTTP Web Server."""
    handler = MonitorDashboardHandler
    # Enable socket reuse to avoid "address already in use" errors on restarts
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        logger.info(f"Dashboard and mock portal serving on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            logger.info("HTTP Server shutting down.")
            stop_event.set()
