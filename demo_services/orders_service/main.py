from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from demo_services.orders_service.clients import (
    validate_user_client,
    reserve_inventory_client,
    process_payment_client
)

app = FastAPI(title="Orders Service", version="0.1.0")

class CreateOrderRequest(BaseModel):
    user_id: str
    item_id: str
    quantity: int
    total_amount: float

class OrderResponse(BaseModel):
    order_id: str
    user_id: str
    item_id: str
    quantity: int
    payment_id: str
    status: str

ORDERS_DB: Dict[str, OrderResponse] = {}

@app.get("/health")
def health():
    return {"status": "ok", "service": "orders-service"}

@app.post("/orders", response_model=OrderResponse)
def create_order(req: CreateOrderRequest):
    try:
        # 1. Validate User
        validate_user_client(req.user_id)
        # 2. Reserve Inventory
        reserve_inventory_client(req.item_id, req.quantity)
        # 3. Process Payment
        pay_res = process_payment_client(req.user_id, req.total_amount)

        order_id = f"ord_{len(ORDERS_DB) + 1000}"
        order = OrderResponse(
            order_id=order_id,
            user_id=req.user_id,
            item_id=req.item_id,
            quantity=req.quantity,
            payment_id=pay_res["payment_id"],
            status="completed"
        )
        ORDERS_DB[order_id] = order
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order processing failed: {str(e)}")

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):
    if order_id not in ORDERS_DB:
        raise HTTPException(status_code=404, detail="Order not found")
    return ORDERS_DB[order_id]
