"""Product Catalog API — FastAPI with Pydantic validation."""

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

app = FastAPI(title="Product Catalog API")

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_products: List[dict] = []
_next_id: int = 1


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ProductIn(BaseModel):
    """Input model for creating / updating a product."""
    name: str = Field(..., min_length=1, description="Product name (non-empty)")
    price: float = Field(..., gt=0, description="Price must be > 0")
    category: str = Field(..., min_length=1, description="Category (non-empty)")


class ProductOut(BaseModel):
    """Output model that includes the generated id."""
    id: int
    name: str
    price: float
    category: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/products", response_model=List[ProductOut])
def list_products(
    category: Optional[str] = Query(None, min_length=1),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> List[ProductOut]:
    """Return paginated, filtered product list."""
    result = list(_products)

    if category:
        result = [p for p in result if p["category"] == category]
    if min_price is not None:
        result = [p for p in result if p["price"] >= min_price]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]

    # Paginate
    start = (page - 1) * limit
    end = start + limit
    return [ProductOut(**p) for p in result[start:end]]


@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int) -> ProductOut:
    """Return a single product by id."""
    for p in _products:
        if p["id"] == product_id:
            return ProductOut(**p)
    raise HTTPException(status_code=404, detail="Product not found")


@app.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductIn) -> ProductOut:
    """Create a new product."""
    global _next_id
    product = {
        "id": _next_id,
        "name": payload.name,
        "price": payload.price,
        "category": payload.category,
    }
    _next_id += 1
    _products.append(product)
    return ProductOut(**product)


@app.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductIn) -> ProductOut:
    """Update an existing product."""
    for idx, p in enumerate(_products):
        if p["id"] == product_id:
            _products[idx] = {
                "id": product_id,
                "name": payload.name,
                "price": payload.price,
                "category": payload.category,
            }
            return ProductOut(**_products[idx])
    raise HTTPException(status_code=404, detail="Product not found")


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int) -> None:
    """Delete a product by id."""
    for idx, p in enumerate(_products):
        if p["id"] == product_id:
            _products.pop(idx)
            return None
    raise HTTPException(status_code=404, detail="Product not found")


# ---------------------------------------------------------------------------
# Health (helps the generic test find a non-parameterised route)
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    """Simple health-check endpoint."""
    return {"status": "ok"}
