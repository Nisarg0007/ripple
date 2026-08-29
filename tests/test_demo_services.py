import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from demo_services.api_gateway.main import app as gateway_app
from demo_services.users_service.main import app as users_app
from demo_services.payment_service.main import app as payment_app
from demo_services.inventory_service.main import app as inventory_app
from demo_services.orders_service.main import app as orders_app

def test_service_health_endpoints():
    client_gw = TestClient(gateway_app)
    assert client_gw.get("/health").json()["service"] == "api-gateway"

    client_users = TestClient(users_app)
    assert client_users.get("/health").json()["service"] == "users-service"

    client_pay = TestClient(payment_app)
    assert client_pay.get("/health").json()["service"] == "payment-service"

    client_inv = TestClient(inventory_app)
    assert client_inv.get("/health").json()["service"] == "inventory-service"

    client_orders = TestClient(orders_app)
    assert client_orders.get("/health").json()["service"] == "orders-service"

def test_users_service_get_user():
    client = TestClient(users_app)
    resp = client.get("/users/user_1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Alice Smith"

def test_payment_service_process_payment():
    client = TestClient(payment_app)
    resp = client.post("/payments", json={"user_id": "user_1", "amount": 250.0})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["amount"] == 250.0

def test_inventory_service_check_and_reserve():
    client = TestClient(inventory_app)
    resp = client.get("/inventory/item_1")
    assert resp.status_code == 200
    assert resp.json()["available_stock"] == 50

    reserve_resp = client.post("/inventory/reserve", json={"item_id": "item_1", "quantity": 5})
    assert reserve_resp.status_code == 200
    assert reserve_resp.json()["status"] == "reserved"

def test_orders_service_orchestration():
    with patch("demo_services.orders_service.main.validate_user_client") as mock_user, \
         patch("demo_services.orders_service.main.reserve_inventory_client") as mock_inv, \
         patch("demo_services.orders_service.main.process_payment_client") as mock_pay:

        mock_user.return_value = {"user_id": "user_1"}
        mock_inv.return_value = {"status": "reserved"}
        mock_pay.return_value = {"payment_id": "pay_999", "status": "success"}

        client = TestClient(orders_app)
        resp = client.post("/orders", json={
            "user_id": "user_1",
            "item_id": "item_1",
            "quantity": 1,
            "total_amount": 99.0
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["payment_id"] == "pay_999"
        assert data["status"] == "completed"
