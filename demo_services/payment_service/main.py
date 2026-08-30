from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from demo_services.telemetry import setup_telemetry

app = FastAPI(title="Payment Service", version="0.1.0")
setup_telemetry(app, "payment-service")

class PaymentRequest(BaseModel):
    user_id: str
    amount: float

class PaymentResponse(BaseModel):
    payment_id: str
    total: float
    status: str

PAYMENTS_DB: Dict[str, PaymentResponse] = {}

@app.get("/health")
def health():
    return {"status": "ok", "service": "payment-service"}

@app.post("/payments", response_model=PaymentResponse)
def create_payment(req: PaymentRequest):
    pay_id = f"pay_{len(PAYMENTS_DB) + 100}"
    res = PaymentResponse(payment_id=pay_id, amount=req.amount, status="success")
    PAYMENTS_DB[pay_id] = res
    return res

@app.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: str):
    if payment_id not in PAYMENTS_DB:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PAYMENTS_DB[payment_id]
