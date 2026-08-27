"""
config.py
Kotak Neo Live Server Configuration
"""

import os
from dotenv import load_dotenv
import pyotp

# Load .env
load_dotenv()

# -------------------------------
# Server
# -------------------------------

PORT = int(os.getenv("PORT", "8787"))

# -------------------------------
# Kotak Credentials
# -------------------------------

KOTAK_CONSUMER_KEY = os.getenv("KOTAK_CONSUMER_KEY")
KOTAK_MOBILE_NUMBER = os.getenv("KOTAK_MOBILE_NUMBER")
KOTAK_UCC = os.getenv("KOTAK_UCC")
KOTAK_MPIN = os.getenv("KOTAK_MPIN")
KOTAK_TOTP_SECRET = os.getenv("KOTAK_TOTP_SECRET")

# -------------------------------
# Database
# -------------------------------

DATABASE_PATH = "data/scrip_master.db"

# -------------------------------
# Cloudflare KV Permanent Storage
# -------------------------------
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "76b5ebb198d3684090f8f560f21231d7")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_KV_NAMESPACE_ID = os.getenv("CLOUDFLARE_KV_NAMESPACE_ID", "cb5b0241ef5e4aec8d8da49bd6fe625d")

# -------------------------------
# Logs
# -------------------------------

LOG_FOLDER = "data/logs"

# -------------------------------
# Websocket
# -------------------------------

MAX_SUBSCRIPTIONS_PER_SOCKET = 200
MAX_SOCKETS = 16

# -------------------------------
# Auto Download
# -------------------------------

DOWNLOAD_SCRIP_MASTER_ON_STARTUP = True

# Download once every day
AUTO_REFRESH_MASTER = True

# -------------------------------
# Auto Login
# -------------------------------

AUTO_RECONNECT = True
AUTO_RELOGIN = True

# -------------------------------
# Analysis Engine
# -------------------------------

# Default scan universe for signals
SCAN_UNIVERSE = os.getenv("SCAN_UNIVERSE", "NIFTY50")  # NIFTY50, NIFTY100, ALL

# Signal scan interval (seconds)
SIGNAL_SCAN_INTERVAL = int(os.getenv("SIGNAL_SCAN_INTERVAL", "300"))

# Technical indicator periods
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# -------------------------------
# Alerts
# -------------------------------

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ENABLE_BROWSER_ALERTS = True
ENABLE_TELEGRAM_ALERTS = bool(os.getenv("TELEGRAM_BOT_TOKEN", ""))

# -------------------------------
# Generate Current TOTP
# -------------------------------

def generate_totp():
    """
    Returns the current 6-digit TOTP.
    """
    if not KOTAK_TOTP_SECRET:
        raise ValueError("KOTAK_TOTP_SECRET not found in .env")

    return pyotp.TOTP(KOTAK_TOTP_SECRET).now()


# -------------------------------
# Validate Required Settings
# -------------------------------

def validate():
    required = {
        "KOTAK_CONSUMER_KEY": KOTAK_CONSUMER_KEY,
        "KOTAK_MOBILE_NUMBER": KOTAK_MOBILE_NUMBER,
        "KOTAK_UCC": KOTAK_UCC,
        "KOTAK_MPIN": KOTAK_MPIN,
        "KOTAK_TOTP_SECRET": KOTAK_TOTP_SECRET,
    }

    missing = [k for k, v in required.items() if not v]

    if missing:
        raise RuntimeError(
            "Missing environment variables:\n"
            + "\n".join(missing)
        )


# -------------------------------
# Startup
# -------------------------------

validate()