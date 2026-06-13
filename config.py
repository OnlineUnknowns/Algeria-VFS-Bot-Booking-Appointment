# src/config.py

# Visa monitoring configuration
VISA_MONITOR_CONFIG = {
    "check_interval_high_demand_seconds": 10,  # 5-10 seconds if allowed
    "check_interval_normal_seconds": 60,   # 30-120 seconds
    "jitter_max_seconds": 5,               # Max random delay to add to interval
}

# Notification settings
NOTIFICATION_CONFIG = {
    "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "telegram_chat_id": "YOUR_TELEGRAM_CHAT_ID",
    "email_sender": "your_email@example.com",
    "email_password": "YOUR_EMAIL_PASSWORD",
    "email_receiver": "recipient_email@example.com",
    "webhook_url": "YOUR_WEBHOOK_URL", # Optional webhook for notifications
}

# User profile data (placeholders - will be managed securely)
USER_PROFILES = {
    "user1": {
        "full_name": "John Doe",
        "passport_number_encrypted": "ENCRYPTED_PASSPORT_NUMBER_HERE",
        "visa_type": "tourism",
        "country": "Italy",
        "preferred_cities": ["Algiers"],
        "booking_url_template": "https://visa.vfsglobal.com/dza/en/ita/apply-visa", # Example URL
    }
}

# Logging settings
LOGGING_CONFIG = {
    "log_file": "agent_activity.log",
    "log_level": "INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL
}
