"""
User Service — Fixes applied:

Bug 1 — GET /users/{id} crashed when user not found (returned None causing AttributeError).
Fix: Check if user exists, raise HTTPException(404) if not.

Bug 2 — POST /users accepted empty names.
Fix: Validate name field is non-empty via Pydantic validator.

Bug 3 — PUT /users/{id} didn't check if user exists (silently created new entry or crashed).
Fix: Check if user exists before updating, raise HTTPException(404) if not.
"""

import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

app = FastAPI(title="User Service")

# In-memory user store
users_db: dict[str, dict] = {}


class UserCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()


class UserUpdate(BaseModel):
    name: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("name must not be empty")
        return v.strip() if v else v


class User(BaseModel):
    id: str
    name: str


def _get_user_or_404(user_id: str) -> dict:
    """Return user dict or raise 404. Fixes Bug 1 & 3 — centralises the check."""
    user = users_db.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


@app.get("/users")
def list_users():
    return {"users": list(users_db.values())}


@app.get("/users/{user_id}")
def get_user(user_id: str):
    """Bug 1: was crashing with 500 when user not found (returned None).
    Now raises proper 404."""
    user = _get_user_or_404(user_id)
    return {"user": user}


@app.post("/users", status_code=201)
def create_user(body: UserCreate):
    """Bug 2: was accepting empty names.
    Now rejects via Pydantic field_validator."""
    user_id = str(uuid.uuid4())
    new_user = {"id": user_id, "name": body.name}
    users_db[user_id] = new_user
    return {"user": new_user}


@app.put("/users/{user_id}")
def update_user(user_id: str, body: UserUpdate):
    """Bug 3: was updating without checking if user exists.
    Now raises 404 if user missing."""
    user = _get_user_or_404(user_id)

    if body.name is not None:
        user["name"] = body.name

    users_db[user_id] = user
    return {"user": user}
