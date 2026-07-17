from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Users CRUD API")


class UserCreate(BaseModel):
    name: str
    email: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


class User(BaseModel):
    id: int
    name: str
    email: str


db: List[User] = []
next_id: int = 1


@app.get("/users", response_model=List[User])
def get_users():
    return db


@app.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate):
    global next_id
    user = User(id=next_id, name=payload.name, email=payload.email)
    db.append(user)
    next_id += 1
    return user


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    for user in db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, payload: UserUpdate):
    for i, user in enumerate(db):
        if user.id == user_id:
            updated = user.model_copy(
                update=payload.model_dump(exclude_unset=True)
            )
            db[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="User not found")


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int):
    for i, user in enumerate(db):
        if user.id == user_id:
            db.pop(i)
            return
    raise HTTPException(status_code=404, detail="User not found")
