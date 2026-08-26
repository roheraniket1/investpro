"""
auth_user.py
Cryptographic User Authentication and Session Token Management for InvestPro
Uses standard library hashlib.pbkdf2_hmac (SHA-256 with 100,000 rounds and per-user salt)
"""

import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

HASH_ITERATIONS = 100_000
SALT_SIZE = 16  # 16 bytes = 128 bits
SESSION_DURATION_DAYS = 90


def sanitize_mobile(mobile: str) -> Optional[str]:
    """Extract standard 10-digit Indian mobile number."""
    if not mobile:
        return None
    # Remove all non-digits
    digits = re.sub(r'\D', '', str(mobile))
    if len(digits) == 10:
        return digits
    if len(digits) == 12 and digits.startswith('91'):
        return digits[2:]
    if len(digits) == 11 and digits.startswith('0'):
        return digits[1:]
    return None


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash password using PBKDF2-HMAC-SHA256.
    Returns (hex_hash, hex_salt).
    """
    if not salt:
        salt_bytes = secrets.token_bytes(SALT_SIZE)
        salt_hex = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt)
        salt_hex = salt

    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        HASH_ITERATIONS
    )
    return key.hex(), salt_hex


def verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    """Verify plaintext password against stored salt and hash."""
    calculated_hash, _ = hash_password(password, salt_hex)
    return secrets.compare_digest(calculated_hash, stored_hash)


def generate_session_token() -> Tuple[str, str]:
    """
    Generate high-entropy session token (64 hex chars).
    Returns (token, expires_at_iso_string).
    """
    token = secrets.token_hex(32)
    expires_at = (datetime.utcnow() + timedelta(days=SESSION_DURATION_DAYS)).isoformat()
    return token, expires_at
