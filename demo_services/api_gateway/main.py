import os
import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from demo_services.telemetry import setup_telemetry

app = FastAPI(title="API Gateway", version="0.1.0")
setup_telemetry(app, "api-gateway")

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
def gateway_create_order(req: GatewayOrderRequest, request: Request):
    url = f"{ORDERS_SERVICE_URL}/orders"
    headers = {
        "x-caller-service": "api-gateway",
        "x-trace-id": request.headers.get("x-trace-id", "")
    }
    resp = httpx.post(url, json=req.model_dump(), headers=headers, timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@app.get("/orders/{order_id}")
def gateway_get_order(order_id: str, request: Request):
    url = f"{ORDERS_SERVICE_URL}/orders/{order_id}"
    headers = {
        "x-caller-service": "api-gateway",
        "x-trace-id": request.headers.get("x-trace-id", "")
    }
    resp = httpx.get(url, headers=headers, timeout=5.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
