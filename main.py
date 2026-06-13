# src/main.py

import time
import random
import json
import logging
from datetime import datetime

from config import VISA_MONITOR_CONFIG, NOTIFICATION_CONFIG, USER_PROFILES, LOGGING_CONFIG

# --- Logging Setup ---
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["log_level"].upper()),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGGING_CONFIG["log_file"]),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# --- Placeholder Functions (to be implemented) ---

def fetch_appointment_availability(country, city, booking_url_template):
    """
    Placeholder: Fetches appointment availability for a given country and city.
    This function must be implemented to interact with the specific visa center website.
    It must adhere to all STRICT RULES.
    """
    logger.info(f"Checking availability for {country}, {city} at {booking_url_template}...")
    # Simulate availability for demonstration purposes
    if random.random() < 0.3: # 30% chance of finding a slot
        available_date = (datetime.now().date() + timedelta(days=random.randint(5, 30))).isoformat()
        logger.info(f"Slot found for {country}, {city} on {available_date}")
        return [{"date": available_date, "type": "new"}]
    else:
        logger.info(f"No slots found for {country}, {city}")
        return []

def send_notification(user_profile, slots_found):
    """
    Placeholder: Sends notifications (Telegram, Email, Webhook) to the user.
    """
    message = f"Visa slot available:\nCountry: {user_profile['country']}\nCenter: {user_profile['preferred_cities'][0]}\nDate: {slots_found[0]['date']}\nLink: {user_profile['booking_url_template']}"
    logger.info(f"Sending notification: {message}")
    # In a real implementation, integrate with Telegram API, Email sender, etc.
    # Example: send_telegram_message(NOTIFICATION_CONFIG["telegram_bot_token"], NOTIFICATION_CONFIG["telegram_chat_id"], message)
    # Example: send_email(NOTIFICATION_CONFIG["email_sender"], NOTIFICATION_CONFIG["email_password"], NOTIFICATION_CONFIG["email_receiver"], "Visa Slot Alert", message)
    pass

def open_booking_page(booking_url):
    """
    Placeholder: Opens the booking page in a browser for manual booking.
    """
    logger.info(f"Opening booking page: {booking_url}")
    # In a real implementation, use a browser automation library (e.g., Selenium, Playwright)
    # Ensure this adheres to website ToS and privacy.
    pass

def store_last_availability_state(user_id, current_slots):
    """
    Placeholder: Stores the last fetched availability state for comparison.
    """
    logger.debug(f"Storing availability state for {user_id}: {current_slots}")
    # In a real implementation, persist this to a file or database
    pass

def get_last_availability_state(user_id):
    """
    Placeholder: Retrieves the last fetched availability state.
    """
    logger.debug(f"Retrieving last availability state for {user_id}")
    # In a real implementation, retrieve from a file or database
    return [] # Return empty for now

# --- Main Monitoring Logic ---

def monitor_visa_slots():
    logger.info("Starting visa slot monitor...")
    last_check_times = {}

    while True:
        for user_id, profile in USER_PROFILES.items():
            current_time = time.time()
            last_check_time = last_check_times.get(user_id, 0)

            # Determine check interval
            # This logic needs refinement based on actual demand and website behavior
            check_interval = VISA_MONITOR_CONFIG["check_interval_normal_seconds"]
            # Add jitter
            effective_check_interval = check_interval + random.uniform(0, VISA_MONITOR_CONFIG["jitter_max_seconds"])

            if (current_time - last_check_time) >= effective_check_interval:
                logger.info(f"Monitoring for user: {user_id}")
                country = profile["country"]
                preferred_city = profile["preferred_cities"][0] # Assuming one preferred city for simplicity
                booking_url = profile["booking_url_template"]

                slots = fetch_appointment_availability(country, preferred_city, booking_url)
                last_known_slots = get_last_availability_state(user_id)

                new_slots = [slot for slot in slots if slot not in last_known_slots]
                canceled_slots = [slot for slot in last_known_slots if slot not in slots]

                if new_slots:
                    logger.info(f"Detected new slots for {user_id}: {new_slots}")
                    send_notification(profile, new_slots)
                    # Optionally open booking page
                    # open_booking_page(booking_url)
                elif canceled_slots:
                    logger.info(f"Detected canceled slots for {user_id}: {canceled_slots}")
                    # Decide if notification is needed for cancellations
                else:
                    logger.info(f"No changes detected for {user_id}.")

                store_last_availability_state(user_id, slots)
                last_check_times[user_id] = current_time

                # Output structured JSON (internal)
                internal_status = "checking"
                if new_slots:
                    internal_status = "available"
                elif not slots:
                    internal_status = "not_available"

                output_json = {
                    "status": internal_status,
                    "slots_found": slots,
                    "last_checked": datetime.now().isoformat(),
                    "next_check_in_seconds": effective_check_interval - (time.time() - current_time)
                }
                logger.debug(f"Internal status: {json.dumps(output_json)}")

        time.sleep(1) # Small sleep to prevent busy-waiting

if __name__ == "__main__":
    from datetime import timedelta
    monitor_visa_slots()
