import os
import httpx

USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8001")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8004")

def validate_user_client(user_id: str) -> dict:
    url = f"{USERS_SERVICE_URL}/users/{user_id}"
    resp = httpx.get(url, timeout=5.0)
    if resp.status_code != 200:
        raise ValueError(f"User validation failed: {resp.text}")
    return resp.json()

def reserve_inventory_client(item_id: str, quantity: int) -> dict:
    url = f"{INVENTORY_SERVICE_URL}/inventory/reserve"
    resp = httpx.post(url, json={"item_id": item_id, "quantity": quantity}, timeout=5.0)
    if resp.status_code != 200:
        raise ValueError(f"Inventory reservation failed: {resp.text}")
    return resp.json()

def process_payment_client(user_id: str, amount: float) -> dict:
    url = f"{PAYMENT_SERVICE_URL}/payments"
    resp = httpx.post(url, json={"user_id": user_id, "amount": amount}, timeout=5.0)
    if resp.status_code != 200:
        raise ValueError(f"Payment execution failed: {resp.text}")
    return resp.json()
