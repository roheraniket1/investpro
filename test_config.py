from config import *

print("Consumer Key :", KOTAK_CONSUMER_KEY)
print("Mobile       :", repr(KOTAK_MOBILE_NUMBER))
print("UCC          :", KOTAK_UCC)
print("MPIN         :", KOTAK_MPIN)
print("TOTP Secret  :", KOTAK_TOTP_SECRET[:5] + "...")