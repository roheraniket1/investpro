"""
websocket_client.py
Live market feed WebSocket client
"""
import threading
import time
from typing import Dict, Any, Callable, List
from logger import get_logger
from auth import get_client

logger = get_logger(__name__)

class MarketFeed:
    def __init__(self):
        self.ticks: Dict[str, dict] = {}
        self.callbacks: List[Callable] = []
        self._connected = False
        self._lock = threading.Lock()
        
    def connect(self, is_reconnect=False):
        """Initialize WebSocket connection."""
        from auth import get_client, reconnect
        
        if is_reconnect:
            try:
                logger.info("Forcing authentication reconnect for fresh credentials...")
                client = reconnect()
            except Exception as re_err:
                logger.error(f"Failed to reconnect client auth: {re_err}")
                client = get_client()
        else:
            client = get_client()
            
        if not client:
            logger.error("Cannot connect WS: No authenticated client")
            return False
            
        try:
            logger.info("Initializing WebSocket connection...")
            client.on_message = self._on_message
            client.on_error = self._on_error
            client.on_close = self._on_close
            client.on_open = self._on_open
            
            return True
        except Exception as e:
            logger.error(f"Error initializing WebSocket: {e}")
            return False

    def _on_message(self, message, *args, **kwargs):
        """Handle incoming tick data."""
        try:
            if isinstance(message, list):
                for tick in message:
                    token = tick.get('instrument_token') or tick.get('token')
                    if token:
                        with self._lock:
                            self.ticks[str(token)] = tick
                        self._trigger_callbacks(tick)
            elif isinstance(message, dict):
                token = message.get('instrument_token') or message.get('token')
                if token:
                    with self._lock:
                        self.ticks[str(token)] = message
                    self._trigger_callbacks(message)
        except Exception as e:
            logger.error(f"Error processing WS message: {e}")

    def _on_error(self, error, *args, **kwargs):
        logger.error(f"WebSocket error: {error} (Args: {args}, Kwargs: {kwargs})")

    def _on_close(self, *args, **kwargs):
        logger.warning(f"WebSocket closed. Args: {args}, Kwargs: {kwargs}")
        self._connected = False
        try:
            from session import session
            session.update(ws_connected=False)
        except Exception:
            pass
        threading.Thread(target=self._auto_reconnect, daemon=True).start()

    def _on_open(self, *args, **kwargs):
        logger.info(f"WebSocket connection opened successfully. Args: {args}, Kwargs: {kwargs}")
        self._connected = True
        try:
            from session import session
            session.update(ws_connected=True)
        except Exception:
            pass
            
        # Restore subscriptions on reconnect
        try:
            from subscribe import subscription_manager
            subscription_manager.restore_subscriptions()
        except Exception as se_err:
            logger.error(f"Failed to restore subscriptions: {se_err}")

    def _auto_reconnect(self):
        """Simple auto-reconnect logic."""
        logger.info("Attempting to reconnect WebSocket in 5 seconds...")
        time.sleep(5)
        self.connect(is_reconnect=True)

    def _trigger_callbacks(self, tick):
        for callback in self.callbacks:
            try:
                callback(tick)
            except Exception as e:
                logger.error(f"Error in tick callback: {e}")

    def get_ltp(self, token: str) -> float:
        """Get last traded price for a token."""
        with self._lock:
            tick = self.ticks.get(str(token), {})
            return tick.get('last_traded_price', tick.get('ltp', 0.0))

    def get_tick(self, token: str) -> dict:
        """Get full tick data for a token."""
        with self._lock:
            return self.ticks.get(str(token), {})

    def get_all_ticks(self) -> dict:
        """Get all current ticks."""
        with self._lock:
            return dict(self.ticks)

    def on_tick(self, callback: Callable):
        """Register external handler for tick data."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)

market_feed = MarketFeed()
