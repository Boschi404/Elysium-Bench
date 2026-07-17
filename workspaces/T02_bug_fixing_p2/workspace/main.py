"""Counter Service — thread-safe concurrent counter."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from threading import Lock

app = FastAPI(title="Counter Service")

# Thread-safe counter using a Lock to prevent race conditions
_counter = 0
_counter_lock = Lock()


class IncrementRequest(BaseModel):
    value: int = Field(default=1, ge=1, description="Amount to increment by")


@app.get("/counter")
def get_counter():
    """Return the current counter value."""
    return JSONResponse(content={"counter": _counter})


@app.post("/increment")
def increment(body: IncrementRequest):
    """Increment the counter by the given value (thread-safe)."""
    global _counter
    try:
        with _counter_lock:
            _counter += body.value
        return JSONResponse(content={"counter": _counter})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
def reset():
    """Reset the counter to zero."""
    global _counter
    with _counter_lock:
        _counter = 0
    return JSONResponse(content={"counter": _counter})
