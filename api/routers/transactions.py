
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from .. import database as db

router = APIRouter(prefix="/transactions", tags=["Transactions"])

class CartItem(BaseModel):
    id: str  # Product ID
    name: str
    qty: int
    price: float
    cost: float
    total: float
    tax_rate: float = 0.0

class TransactionCreate(BaseModel):
    account_id: str
    items: List[CartItem]
    total_amount: float
    total_profit: float
    payment_method: str = "CASH"
    customer_id: Optional[str] = None
    points_redeemed: int = 0
    doctor_name: Optional[str] = None
    doctor_reg_no: Optional[str] = None

@router.post("/")
async def create_transaction(txn: TransactionCreate):
    txn_id = await db.record_transaction_async(txn)
    if not txn_id:
        raise HTTPException(status_code=500, detail="Transaction failed")
    return {"id": txn_id, "status": "success"}
