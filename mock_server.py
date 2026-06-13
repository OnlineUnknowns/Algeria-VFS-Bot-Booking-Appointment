# src/mock_server.py

import json
import os
from datetime import datetime

MOCK_SLOTS_FILE = os.path.join(os.path.dirname(__file__), "mock_slots.json")

DEFAULT_SLOTS = [
    {"date": "2026-07-20", "city": "Algiers", "country": "Italy", "type": "tourism"},
    {"date": "2026-08-05", "city": "Oran", "country": "Italy", "type": "tourism"},
]

def load_mock_slots():
    """Loads current mock slots from file, or initializes with defaults."""
    if os.path.exists(MOCK_SLOTS_FILE):
        try:
            with open(MOCK_SLOTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_SLOTS.copy()
    else:
        save_mock_slots(DEFAULT_SLOTS)
        return DEFAULT_SLOTS.copy()

def save_mock_slots(slots):
    """Saves mock slots list to file."""
    with open(MOCK_SLOTS_FILE, "w") as f:
        json.dump(slots, f, indent=4)

def handle_mock_availability_html(city="Algiers"):
    """
    Generates a realistic VFS-style HTML page showing current slot availability.
    This page is designed to be parsed by BeautifulSoup.
    """
    slots = load_mock_slots()
    # Filter slots by city if requested
    filtered_slots = [s for s in slots if s["city"].lower() == city.lower()]
    
    rows_html = ""
    if filtered_slots:
        for slot in sorted(filtered_slots, key=lambda x: x["date"]):
            rows_html += f"""
            <tr class="slot-row">
                <td class="col-date">{slot["date"]}</td>
                <td class="col-location">{slot["city"]}</td>
                <td class="col-country">{slot["country"]}</td>
                <td class="col-type">{slot["type"].capitalize()}</td>
                <td class="col-status"><span class="badge available">Available</span></td>
                <td class="col-action"><a href="/mock/vfs/italy/book?date={slot["date"]}&city={slot["city"]}" class="btn-book">Book Now</a></td>
            </tr>
            """
    else:
        rows_html = """
        <tr>
            <td colspan="6" class="no-slots">No visa appointment slots are currently available for this selection. Please check back later.</td>
        </tr>
        """
        
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>VFS Global - Italy Visa Center Algeria</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 0; }}
        header {{ background-color: #e87722; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 4px solid #1f3a60; }}
        header h1 {{ margin: 0; font-size: 20px; }}
        .container {{ max-width: 1000px; margin: 30px auto; padding: 20px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 4px; }}
        h2 {{ color: #1f3a60; border-bottom: 2px solid #e87722; padding-bottom: 8px; margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background-color: #1f3a60; color: white; text-align: left; padding: 12px; font-size: 14px; }}
        td {{ padding: 12px; border-bottom: 1px solid #ddd; font-size: 14px; }}
        tr:hover {{ background-color: #f1f3f5; }}
        .badge {{ padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; text-transform: uppercase; }}
        .badge.available {{ background-color: #d4edda; color: #155724; }}
        .btn-book {{ background-color: #e87722; color: white; text-decoration: none; padding: 6px 12px; border-radius: 3px; font-size: 12px; font-weight: bold; transition: background 0.2s; }}
        .btn-book:hover {{ background-color: #cb6316; }}
        .no-slots {{ text-align: center; color: #6c757d; padding: 30px; font-style: italic; }}
        .footer {{ text-align: center; font-size: 12px; color: #6c757d; margin-top: 50px; padding: 20px; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <header>
        <h1>VFS GLOBAL <span style="font-weight: 300;">| PARTNERING WITH GOVERNMENTS</span></h1>
        <div style="font-size: 14px; font-weight: bold;">Algeria Portal - Italy Visa</div>
    </header>
    <div class="container">
        <h2>Appointment Availability (Live Status)</h2>
        <p>This page displays official, publicly accessible visa appointment slots for Italy in Algeria. Slots are updated in real-time.</p>
        
        <table id="slots-table">
            <thead>
                <tr>
                    <th>Appointment Date</th>
                    <th>Visa Center</th>
                    <th>Country</th>
                    <th>Visa Category</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    <div class="footer">
        &copy; 2026 VFS Global Group. All rights reserved. Compliant with Terms of Service.
    </div>
</body>
</html>
"""
    return html

def handle_mock_booking_html(date="", city="", name="", passport="", visa_type=""):
    """
    Generates a simulated booking page form that can be pre-filled.
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>VFS Global - Italy Visa Appointment Booking</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 0; }}
        header {{ background-color: #e87722; color: white; padding: 15px 30px; border-bottom: 4px solid #1f3a60; }}
        header h1 {{ margin: 0; font-size: 20px; }}
        .container {{ max-width: 600px; margin: 30px auto; padding: 30px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 4px; }}
        h2 {{ color: #1f3a60; margin-top: 0; border-bottom: 2px solid #e87722; padding-bottom: 8px; }}
        .form-group {{ margin-bottom: 18px; }}
        label {{ display: block; font-weight: bold; margin-bottom: 6px; font-size: 13px; color: #495057; }}
        input, select {{ width: 100%; padding: 10px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; box-sizing: border-box; }}
        input:focus, select:focus {{ border-color: #e87722; outline: none; box-shadow: 0 0 0 2px rgba(232, 119, 34, 0.25); }}
        .row {{ display: flex; gap: 15px; }}
        .row .form-group {{ flex: 1; }}
        .btn-submit {{ background-color: #1f3a60; color: white; border: none; padding: 12px 20px; font-size: 15px; font-weight: bold; border-radius: 4px; cursor: pointer; width: 100%; transition: background 0.2s; margin-top: 10px; }}
        .btn-submit:hover {{ background-color: #152842; }}
        .info-banner {{ background-color: #e2f0fd; border-left: 4px solid #0066cc; color: #004085; padding: 12px; border-radius: 4px; margin-bottom: 20px; font-size: 13px; }}
    </style>
</head>
<body>
    <header>
        <h1>VFS GLOBAL <span style="font-weight: 300;">| PARTNERING WITH GOVERNMENTS</span></h1>
    </header>
    <div class="container">
        <h2>Secure Visa Appointment Booking</h2>
        <div class="info-banner">
            You are booking an appointment for <strong>Italy Visa ({visa_type.capitalize()})</strong> at <strong>VFS {city}</strong> on <strong>{date}</strong>.
        </div>
        
        <form onsubmit="alert('Simulated Booking Successful! Your appointment reference is VFS-ITA-981247.'); return false;">
            <div class="form-group">
                <label for="fullname">Full Name (as in Passport)</label>
                <input type="text" id="fullname" value="{name}" required placeholder="e.g. John Doe">
            </div>
            
            <div class="form-group">
                <label for="passport">Passport Number</label>
                <input type="text" id="passport" value="{passport}" required placeholder="e.g. A12345678">
            </div>
            
            <div class="row">
                <div class="form-group">
                    <label for="visa_type">Visa Category</label>
                    <select id="visa_type">
                        <option value="tourism" {"selected" if visa_type == "tourism" else ""}>Tourism</option>
                        <option value="study" {"selected" if visa_type == "study" else ""}>Study</option>
                        <option value="business" {"selected" if visa_type == "business" else ""}>Business</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="city">Center</label>
                    <input type="text" id="city" value="{city}" readonly>
                </div>
            </div>
            
            <div class="form-group">
                <label for="date">Selected Date</label>
                <input type="text" id="date" value="{date}" readonly>
            </div>
            
            <button type="submit" class="btn-submit">Confirm Appointment Booking</button>
        </form>
    </div>
</body>
</html>
"""
    return html
