from neo_api_client import NeoAPI
import inspect

print("totp_login:")
print(inspect.signature(NeoAPI.totp_login))

print("\n")

print("totp_validate:")
print(inspect.signature(NeoAPI.totp_validate))