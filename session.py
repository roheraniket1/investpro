"""
session.py
Runtime session storage (thread-safe)
"""
import threading
from typing import Any

class SessionManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._session_data = {
            "view_token": None,
            "view_sid": None,
            "trade_token": None,
            "trade_sid": None,
            "base_url": None,
            "data_center": None,
            "ws_connected": False,
            "login_time": None,
            "last_activity": None
        }

    def update(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items():
                self._session_data[key] = value

    def get(self, key: str) -> Any:
        with self._lock:
            return self._session_data.get(key)

    def is_active(self) -> bool:
        with self._lock:
            return bool(self._session_data.get("view_token"))

    def clear(self):
        with self._lock:
            for key in self._session_data:
                if isinstance(self._session_data[key], bool):
                    self._session_data[key] = False
                else:
                    self._session_data[key] = None

    def to_dict(self) -> dict:
        with self._lock:
            return dict(self._session_data)

session = SessionManager()
