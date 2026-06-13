# src/notifications.py

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import logging

logger = logging.getLogger(__name__)

def send_telegram_notification(token: str, chat_id: str, message: str) -> bool:
    """
    Sends a message to the specified Telegram chat ID using the bot token.
    """
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN" or not chat_id or chat_id == "YOUR_TELEGRAM_CHAT_ID":
        logger.warning("Telegram notification skipped: credentials not configured.")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        res_data = response.json()
        if res_data.get("ok"):
            logger.info("Telegram notification sent successfully.")
            return True
        else:
            logger.error(f"Telegram API error: {res_data}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False

def send_email_notification(smtp_server: str, port: int, sender_email: str, sender_password: str, receiver_email: str, subject: str, body_html: str, body_text: str = "") -> bool:
    """
    Sends an email notification using SMTP. Supports TLS or SSL.
    """
    if not sender_email or sender_email == "your_email@example.com" or not receiver_email or receiver_email == "recipient_email@example.com" or not sender_password:
        logger.warning("Email notification skipped: SMTP credentials not configured.")
        return False
        
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email
        
        # Record the MIME types
        if body_text:
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)
        part2 = MIMEText(body_html, 'html')
        msg.attach(part2)
        
        # Connect and authenticate
        # Determine port for SSL vs STARTTLS
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_server, port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_server, port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        logger.info("Email notification sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return False

def send_webhook_notification(webhook_url: str, slot_data: dict) -> bool:
    """
    Sends a JSON POST webhook notification to a configured endpoint.
    """
    if not webhook_url or webhook_url == "YOUR_WEBHOOK_URL":
        logger.debug("Webhook notification skipped: URL not configured.")
        return False
        
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, json=slot_data, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("Webhook notification triggered successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to send webhook notification: {e}")
        return False

def dispatch_slot_alert(profile: dict, notifications_config: dict, new_slots: list) -> int:
    """
    Formulates messages and dispatches notifications across all configured channels
    for a list of newly available slots.
    Returns the count of successfully sent notifications.
    """
    if not new_slots:
        return 0
        
    success_count = 0
    country = profile.get("country", "N/A")
    city = profile.get("preferred_cities", ["N/A"])[0]
    booking_url = profile.get("booking_url_template", "")
    
    # Formulate messages
    # 1. Simple text notification
    dates_str = ", ".join([slot["date"] for slot in new_slots])
    visa_types_str = ", ".join(list(set([slot.get("type", "tourism").capitalize() for slot in new_slots])))
    
    text_msg = (
        f"<b>Visa slot available:</b>\n"
        f"Country: {country}\n"
        f"Center: {city}\n"
        f"Dates: {dates_str}\n"
        f"Visa Category: {visa_types_str}\n"
        f"Link: {booking_url}"
    )
    
    # Send Telegram
    tg_token = notifications_config.get("telegram_bot_token")
    tg_chat_id = notifications_config.get("telegram_chat_id")
    if tg_token and tg_chat_id:
        if send_telegram_notification(tg_token, tg_chat_id, text_msg):
            success_count += 1
            
    # Send Email
    email_sender = notifications_config.get("email_sender")
    email_password = notifications_config.get("email_password")
    email_receiver = notifications_config.get("email_receiver")
    smtp_server = notifications_config.get("email_smtp_server", "smtp.gmail.com")
    smtp_port = int(notifications_config.get("email_smtp_port", 587))
    
    if email_sender and email_password and email_receiver:
        subject = f"Visa Slot Alert: {country} in {city} Available!"
        html_msg = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #1f3a60; border-bottom: 2px solid #e87722; padding-bottom: 10px;">Visa Slot Available Alert</h2>
                <p>Great news! New visa appointment slots have been detected.</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f2f2f2;">
                        <td style="padding: 10px; font-weight: bold;">Country</td>
                        <td style="padding: 10px;">{country}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; font-weight: bold;">Visa Center</td>
                        <td style="padding: 10px;">{city}</td>
                    </tr>
                    <tr style="background-color: #f2f2f2;">
                        <td style="padding: 10px; font-weight: bold;">Visa Category</td>
                        <td style="padding: 10px;">{visa_types_str}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; font-weight: bold;">Available Dates</td>
                        <td style="padding: 10px; color: #28a745; font-weight: bold;">{dates_str}</td>
                    </tr>
                </table>
                <p style="text-align: center; margin-top: 30px;">
                    <a href="{booking_url}" style="background-color: #e87722; color: white; text-decoration: none; padding: 12px 24px; font-weight: bold; border-radius: 4px; display: inline-block;">Go to Booking Page</a>
                </p>
                <p style="font-size: 11px; color: #777; margin-top: 40px; border-top: 1px solid #eee; padding-top: 10px;">
                    Sent automatically by your AI Visa Monitor Agent.
                </p>
            </div>
        </body>
        </html>
        """
        text_alt = f"Visa Slot Available!\nCountry: {country}\nCenter: {city}\nDates: {dates_str}\nLink: {booking_url}"
        if send_email_notification(smtp_server, smtp_port, email_sender, email_password, email_receiver, subject, html_msg, text_alt):
            success_count += 1
            
    # Send Webhook
    webhook_url = notifications_config.get("webhook_url")
    if webhook_url:
        payload = {
            "event": "slot_detected",
            "country": country,
            "city": city,
            "slots": new_slots,
            "booking_url": booking_url
        }
        if send_webhook_notification(webhook_url, payload):
            success_count += 1
            
    return success_count
