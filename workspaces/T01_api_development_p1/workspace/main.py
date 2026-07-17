"""User CRUD REST API built with FastAPI.

Endpoints:
    GET    /users      — List all users
    GET    /users/{id} — Get a single user by ID
    POST   /users      — Create a new user
    PUT    /users/{id} — Update an existing user
    DELETE /users/{id} — Delete a user

In-memory storage. Input validation via Pydantic models.
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="User CRUD API")

# ---------------------------------------------------------------------------
# In-memory storage
# ---------------------------------------------------------------------------

_users_db: dict[int, dict] = {}
_next_id: int = 1

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

_EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


def _validate_email(value: str) -> str:
    """Validate email format. Raises ValueError on invalid input."""
    if not re.match(_EMAIL_PATTERN, value):
        raise ValueError("Invalid email format")
    return value


class UserCreate(BaseModel):
    """Request body for creating a user."""

    name: str = Field(..., min_length=3, description="Name must be longer than 2 characters")
    email: str = Field(..., description="Valid email address")
    age: int = Field(..., gt=0, description="Age must be greater than 0")

    _validate_email = field_validator("email")(_validate_email)


class UserUpdate(BaseModel):
    """Request body for updating a user. All fields optional."""

    name: Optional[str] = Field(None, min_length=3, description="Name must be longer than 2 characters")
    email: Optional[str] = Field(None, description="Valid email address")
    age: Optional[int] = Field(None, gt=0, description="Age must be greater than 0")

    _validate_email = field_validator("email")(_validate_email)


class UserOut(BaseModel):
    """Response body for a user."""

    id: int
    name: str
    email: str
    age: int


def _user_to_out(user_id: int, user_data: dict) -> UserOut:
    """Convert internal storage dict to a UserOut response model."""
    return UserOut(id=user_id, **user_data)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/users", response_model=list[UserOut], status_code=status.HTTP_200_OK)
def list_users():
    """Return all users."""
    return [_user_to_out(uid, data) for uid, data in _users_db.items()]


@app.get("/users/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_user(user_id: int):
    """Return a single user by ID."""
    user_data = _users_db.get(user_id)
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_to_out(user_id, user_data)


@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate):
    """Create a new user."""
    global _next_id
    new_id = _next_id
    _next_id += 1
    _users_db[new_id] = body.model_dump()
    return _user_to_out(new_id, _users_db[new_id])


@app.put("/users/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
def update_user(user_id: int, body: UserUpdate):
    """Update an existing user. Partial updates supported."""
    user_data = _users_db.get(user_id)
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update",
        )
    user_data.update(update_data)
    return _user_to_out(user_id, user_data)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int):
    """Delete a user by ID."""
    if user_id not in _users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    del _users_db[user_id]
    return None
