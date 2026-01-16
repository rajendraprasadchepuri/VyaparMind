
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .. import database as db

router = APIRouter(prefix="/products", tags=["Products"])

class ProductCreate(BaseModel):
    account_id: str
    name: str
    category: str
    price: float
    cost_price: float
    stock_quantity: int
    tax_rate: float = 0.0
    salt_composition: Optional[str] = None
    manufacturer: Optional[str] = None
    schedule_type: Optional[str] = None
    is_chronic: int = 0
    refill_interval: int = 30

from ..cache import cache

@router.get("/")
async def list_products(account_id: str, search: str = None, limit: int = 50):
    cache_key = f"inventory:{account_id}:{search or 'all'}:{limit}"
    
    # Try Cache
    cached = await cache.get(cache_key)
    if cached:
        return cached
        
    # DB Call
    data = await db.fetch_pos_inventory(account_id, search, limit)
    
    # Set Cache (Limit TTL to 1 minute as stock changes often)
    await cache.set(cache_key, data, ttl=60)
    
    return data

@router.post("/")
async def add_new_product(product: ProductCreate):
    # We need to implement add_product in database.py
    # Generating ID here or in DB? Best in DB/Logic layer.
    import secrets
    import string
    chars = string.ascii_uppercase + string.digits
    new_id = ''.join(secrets.choice(chars) for _ in range(16))
    
    success, msg = await db.add_product_async(
        product.account_id, new_id, product.name, product.category,
        product.price, product.cost_price, product.stock_quantity,
        product.tax_rate, product.salt_composition, product.manufacturer,
        product.schedule_type, product.is_chronic, product.refill_interval
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"id": new_id, "message": msg}

@router.get("/{product_id}")
async def get_product(product_id: str):
    prod = await db.get_product_by_id_async(product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    # Wrap in list or return dict? Client expects dict.
    return prod
