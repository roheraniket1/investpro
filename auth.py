"""
auth.py
Kotak Neo Authentication
"""

import logging
import time

try:
    from neo_api_client import NeoAPI
    NEO_AVAILABLE = True
except ImportError:
    NeoAPI = None
    NEO_AVAILABLE = False

from config import (
    KOTAK_CONSUMER_KEY,
    KOTAK_MOBILE_NUMBER,
    KOTAK_UCC,
    KOTAK_MPIN,
    generate_totp,
)

logger = logging.getLogger("KotakAuth")


class KotakAuth:

    def __init__(self):
        self.client = None
        self.logged_in = False

    def login(self):
        """
        Login using TOTP + MPIN
        """

        if not NEO_AVAILABLE:
            logger.warning("neo-api-client not installed. Running in analysis-only mode.")
            self.logged_in = False
            return None

        logger.info("Creating NeoAPI client...")

        self.client = NeoAPI(
            consumer_key=KOTAK_CONSUMER_KEY,
            environment="prod"
        )

        totp = generate_totp()

        print("\nGenerated TOTP:", totp)

        logger.info("Logging in...")

        login_response = self.client.totp_login(
            mobile_number=KOTAK_MOBILE_NUMBER,
            ucc=KOTAK_UCC,
            totp=totp
        )

        print("\nLOGIN RESPONSE:")
        print(login_response)

        logger.info("Validating MPIN...")

        validate_response = self.client.totp_validate(
            mpin=KOTAK_MPIN
        )

        print("\nVALIDATE RESPONSE:")
        print(validate_response)

        print("\nCLIENT CONFIGURATION:")
        try:
            print(self.client.configuration.__dict__)
        except Exception:
            print(self.client.configuration)

        # Update SessionManager
        try:
            from session import session
            import datetime
            
            if isinstance(login_response, dict) and "data" in login_response:
                data = login_response["data"]
                session.update(
                    view_token=data.get("token"),
                    view_sid=data.get("sid")
                )
                
            if isinstance(validate_response, dict) and "data" in validate_response:
                data = validate_response["data"]
                session.update(
                    trade_token=data.get("token"),
                    trade_sid=data.get("sid"),
                    base_url=data.get("baseUrl"),
                    data_center=data.get("dataCenter"),
                    login_time=datetime.datetime.now().isoformat(),
                    last_activity=datetime.datetime.now().isoformat()
                )
        except Exception as se:
            logger.error(f"Failed to update session storage: {se}")

        self.logged_in = True

        logger.info("Kotak login successful.")

        return self.client

    def reconnect(self):
        """
        Re-login after disconnect/session expiry.
        """

        logger.warning("Session expired. Reconnecting...")

        self.logged_in = False

        retry = 0

        while retry < 5:

            try:

                self.login()

                logger.info("Reconnected successfully.")

                return self.client

            except Exception as e:

                retry += 1

                logger.error(f"Reconnect failed ({retry}/5): {e}")

                time.sleep(5)

        raise RuntimeError("Unable to reconnect to Kotak Neo.")

    def get_client(self):

        if self.client is None:
            return self.login()

        return self.client


auth = KotakAuth()


def get_client():
    return auth.get_client()


def reconnect():
    return auth.reconnect()