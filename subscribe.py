"""
subscribe.py
Dynamic subscription manager
"""
import threading
from typing import List, Union
from logger import get_logger
from auth import get_client
from database import db
from websocket_client import market_feed

logger = get_logger(__name__)

# Fallback config if not found
try:
    from config import MAX_SUBSCRIPTIONS_PER_SOCKET
except ImportError:
    MAX_SUBSCRIPTIONS_PER_SOCKET = 200

class SubscriptionManager:
    def __init__(self):
        self._active_subscriptions = set()
        self._lock = threading.Lock()

    def _resolve_tokens(self, items: List[str]) -> List[dict]:
        """Resolve symbols to instrument tokens formatting required by NeoAPI."""
        resolved = []
        for item in items:
            if str(item).isdigit():
                row = db.get_by_token(item)
                if row:
                    resolved.append({"instrument_token": str(item), "exchange_segment": row.get("segment", "nse_cm")})
                else:
                    resolved.append({"instrument_token": str(item), "exchange_segment": "nse_cm"})
            else:
                token = db.get_token(item)
                if token:
                    row = db.get_by_token(token)
                    resolved.append({"instrument_token": str(token), "exchange_segment": row.get("segment", "nse_cm")})
                else:
                    logger.warning(f"Could not resolve symbol {item} to token")
        return resolved

    def subscribe(self, tokens_or_symbols: Union[str, List[str]]) -> bool:
        """Subscribe to live data."""
        if isinstance(tokens_or_symbols, str):
            tokens_or_symbols = [tokens_or_symbols]
            
        client = get_client()
        if not client:
            logger.error("Cannot subscribe: No authenticated client")
            return False

        instruments = self._resolve_tokens(tokens_or_symbols)
        if not instruments:
            logger.warning("No valid instruments to subscribe")
            return False

        with self._lock:
            if len(self._active_subscriptions) + len(instruments) > MAX_SUBSCRIPTIONS_PER_SOCKET:
                logger.warning(f"Subscription limit ({MAX_SUBSCRIPTIONS_PER_SOCKET}) reached.")
                
            try:
                client.subscribe(instrument_tokens=instruments, isIndex=False, isDepth=False)
                for inst in instruments:
                    self._active_subscriptions.add(inst["instrument_token"])
                logger.info(f"Subscribed to {len(instruments)} instruments")
                return True
            except Exception as e:
                logger.error(f"Subscription failed: {e}")
                return False

    def unsubscribe(self, tokens_or_symbols: Union[str, List[str]]) -> bool:
        """Unsubscribe from live data."""
        if isinstance(tokens_or_symbols, str):
            tokens_or_symbols = [tokens_or_symbols]
            
        client = get_client()
        if not client:
            return False

        instruments = self._resolve_tokens(tokens_or_symbols)
        if not instruments:
            return False

        with self._lock:
            try:
                client.un_subscribe(instrument_tokens=instruments, isIndex=False, isDepth=False)
                for inst in instruments:
                    self._active_subscriptions.discard(inst["instrument_token"])
                logger.info(f"Unsubscribed from {len(instruments)} instruments")
                return True
            except Exception as e:
                logger.error(f"Unsubscribe failed: {e}")
                return False

    def get_active(self) -> List[str]:
        """List active subscriptions."""
        with self._lock:
            return list(self._active_subscriptions)

    def restore_subscriptions(self) -> bool:
        """Re-subscribe to all active subscriptions on socket reconnect."""
        client = get_client()
        if not client:
            return False
        with self._lock:
            if not self._active_subscriptions:
                return True
            instruments = self._resolve_tokens(list(self._active_subscriptions))
            try:
                # Re-subscribe
                client.subscribe(instrument_tokens=instruments, isIndex=False, isDepth=False)
                logger.info(f"Restored {len(instruments)} active subscriptions on WebSocket reconnect.")
                return True
            except Exception as e:
                logger.error(f"Failed to restore subscriptions: {e}")
                return False

    def subscribe_index(self, index_name: str) -> bool:
        """Subscribe to index like Nifty 50"""
        client = get_client()
        if not client:
            return False
            
        indices = {
            "NIFTY 50": {"instrument_token": "26000", "exchange_segment": "nse_cm"},
            "NIFTY": {"instrument_token": "26000", "exchange_segment": "nse_cm"},
            "BANKNIFTY": {"instrument_token": "26009", "exchange_segment": "nse_cm"},
            "BANK NIFTY": {"instrument_token": "26009", "exchange_segment": "nse_cm"}
        }
        
        index_upper = index_name.upper()
        if index_upper in indices:
            try:
                client.subscribe(instrument_tokens=[indices[index_upper]], isIndex=True, isDepth=False)
                self._active_subscriptions.add(indices[index_upper]["instrument_token"])
                logger.info(f"Subscribed to index: {index_name}")
                return True
            except Exception as e:
                logger.error(f"Index subscription failed: {e}")
        else:
            logger.warning(f"Unknown index: {index_name}")
            
        return False

subscription_manager = SubscriptionManager()
