
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .. import database as db

router = APIRouter(prefix="/customers", tags=["Customers"])

class CustomerCreate(BaseModel):
    account_id: str
    name: str
    phone: str
    email: Optional[str] = None
    city: Optional[str] = "Unknown"
    pincode: Optional[str] = "000000"

@router.get("/phone/{phone}")
async def get_customer(account_id: str, phone: str):
    cust = await db.get_customer_by_phone_async(account_id, phone)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")
    return cust

@router.post("/")
async def create_customer(cust: CustomerCreate):
    # Determine ID logic (manual or auto). POS uses random numeric usually.
    import secrets
    import string
    chars = string.digits
    new_id = ''.join(secrets.choice(chars) for _ in range(16))
    
    success, msg = await db.add_customer(cust.account_id, new_id, cust.name, cust.phone, cust.email)
    if not success:
         raise HTTPException(status_code=400, detail=msg)
    return {"id": new_id, "message": msg}
