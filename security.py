# src/security.py

import os
from cryptography.fernet import Fernet

KEY_FILE = os.path.join(os.path.dirname(__file__), "secret.key")

def get_or_create_key():
    """
    Retrieves the encryption key from secret.key, or creates one if it doesn't exist.
    """
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key

def encrypt_data(data: str) -> str:
    """
    Encrypts a string and returns the base64 encrypted string.
    """
    if not data:
        return ""
    key = get_or_create_key()
    fernet = Fernet(key)
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypts an encrypted base64 string and returns the plaintext.
    """
    if not encrypted_data:
        return ""
    try:
        key = get_or_create_key()
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        # If decryption fails, return a placeholder or empty string
        return f"DECRYPTION_ERROR: {str(e)}"

def mask_passport(passport: str) -> str:
    """
    Masks a passport number to protect user privacy in UI representations.
    e.g., AB1234567 -> AB*****67
    """
    if not passport:
        return ""
    if len(passport) <= 4:
        return "****"
    return f"{passport[:2]}{'*' * (len(passport) - 4)}{passport[-2:]}"
