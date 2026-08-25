from neo_api_client import NeoAPI
from config import KOTAK_CONSUMER_KEY, KOTAK_UCC, KOTAK_MPIN, generate_totp

client = NeoAPI(
    consumer_key=KOTAK_CONSUMER_KEY,
    environment="prod"
)

totp = generate_totp()
print("TOTP:", totp)

print("Trying login with +91 + 9265708153...")
login_response = client.totp_login(
    mobile_number="+919265708153",
    ucc=KOTAK_UCC,
    totp=totp
)
print("LOGIN RESPONSE:")
print(login_response)

if "error" not in str(login_response):
    print("Trying validate...")
    validate_response = client.totp_validate(mpin=KOTAK_MPIN)
    print("VALIDATE RESPONSE:")
    print(validate_response)
