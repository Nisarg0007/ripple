from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Users Service", version="0.1.0")

class User(BaseModel):
    user_id: str
    name: str
    email: str

USERS_DB = {
    "user_1": User(user_id="user_1", name="Alice Smith", email="alice@example.com"),
    "user_2": User(user_id="user_2", name="Bob Jones", email="bob@example.com"),
}

@app.get("/health")
def health():
    return {"status": "ok", "service": "users-service"}

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: str):
    if user_id not in USERS_DB:
        raise HTTPException(status_code=404, detail="User not found")
    return USERS_DB[user_id]
