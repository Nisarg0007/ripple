# Ripple Demo Microservices

This directory contains a lightweight, realistic microservice system designed to demonstrate **Ripple's** change impact analysis and dependency discovery capabilities.

---

## 🏗️ Architecture & Component Topology

```text
                           +-----------------+
                           |   API Gateway   | (Port 8000)
                           +--------+--------+
                                    |
                 +------------------+------------------+
                 |                  |                  |
                 v                  v                  v
         +---------------+  +---------------+  +---------------+
         | Users Service |  | Orders Service|  |Inventory Serv.|
         |  (Port 8001)  |  |  (Port 8002)  |  |  (Port 8004)  |
         +---------------+  +-------+-------+  +---------------+
                                    |
                                    v
                            +---------------+
                            |Payment Service|
                            |  (Port 8003)  |
                            +---------------+
```

---

## 📡 Microservice Interfaces & Ports

1. **API Gateway (`port 8000`)**:
   - `GET /health`
   - `POST /orders`
   - `GET /orders/{order_id}`

2. **Users Service (`port 8001`)**:
   - `GET /health`
   - `GET /users/{user_id}`

3. **Orders Service (`port 8002`)**:
   - `GET /health`
   - `POST /orders`
   - `GET /orders/{order_id}`

4. **Payment Service (`port 8003`)**:
   - `GET /health`
   - `POST /payments`
   - `GET /payments/{payment_id}`

5. **Inventory Service (`port 8004`)**:
   - `GET /health`
   - `GET /inventory/{item_id}`
   - `POST /inventory/reserve`

---

## 🚀 How to Run Locally

### Option 1: Docker Compose
```bash
docker-compose -f demo-services/docker-compose.yml up --build
```

### Option 2: Local Python Execution
Start each service in a separate terminal window:
```bash
uvicorn demo_services.api_gateway.main:app --port 8000
uvicorn demo_services.users_service.main:app --port 8001
uvicorn demo_services.orders_service.main:app --port 8002
uvicorn demo_services.payment_service.main:app --port 8003
uvicorn demo_services.inventory_service.main:app --port 8004
```

---

## 🧪 Testing Order Processing Flow

Submit an order through the API Gateway:
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_1",
    "item_id": "item_1",
    "quantity": 2,
    "total_amount": 100.0
  }'
```
Expected Response:
```json
{
  "order_id": "ord_1000",
  "user_id": "user_1",
  "item_id": "item_1",
  "quantity": 2,
  "payment_id": "pay_100",
  "status": "completed"
}
```
