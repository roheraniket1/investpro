from auth import get_client

client = get_client()

try:
    result = client.scrip_master(exchange_segment="nse_cm")
    print(type(result))
    print(result)
except Exception as e:
    print("ERROR:", e)