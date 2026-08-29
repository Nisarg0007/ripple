import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="API Gateway", version="0.1.0")

ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL", "http://localhost:8002")

class GatewayOrderRequest(BaseModel):
    user_id: str
    item_id: str
    quantity: int
    total_amount: float

@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}

@app.post("/orders")
def gateway_create_order(req: GatewayOrderRequest):
    url = f"{ORDERS_SERVICE_URL}/orders"
    resp = httpx.post(url, json=req.model_dump(), timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@app.get("/orders/{order_id}")
def gateway_get_order(order_id: str):
    url = f"{ORDERS_SERVICE_URL}/orders/{order_id}"
    resp = httpx.get(url, timeout=5.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
