from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from demo_services.telemetry import setup_telemetry

app = FastAPI(title="Inventory Service", version="0.1.0")
setup_telemetry(app, "inventory-service")

class Item(BaseModel):
    item_id: str
    name: str
    available_stock: int

class ReserveRequest(BaseModel):
    item_id: str
    quantity: int

class ReserveResponse(BaseModel):
    item_id: str
    quantity: int
    status: str

INVENTORY_DB: Dict[str, Item] = {
    "item_1": Item(item_id="item_1", name="Wireless Mouse", available_stock=50),
    "item_2": Item(item_id="item_2", name="Mechanical Keyboard", available_stock=20),
}

@app.get("/health")
def health():
    return {"status": "ok", "service": "inventory-service"}

@app.get("/inventory/{item_id}", response_model=Item)
def get_inventory(item_id: str):
    if item_id not in INVENTORY_DB:
        raise HTTPException(status_code=404, detail="Item not found")
    return INVENTORY_DB[item_id]

@app.post("/inventory/reserve", response_model=ReserveResponse)
def reserve_inventory(req: ReserveRequest):
    if req.item_id not in INVENTORY_DB:
        raise HTTPException(status_code=404, detail="Item not found")
    item = INVENTORY_DB[req.item_id]
    if item.available_stock < req.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    item.available_stock -= req.quantity
    return ReserveResponse(item_id=req.item_id, quantity=req.quantity, status="reserved")
