
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import database as db

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingUpdate(BaseModel):
    account_id: str
    key: str
    value: str

@router.get("/{key}")
async def get_setting(account_id: str, key: str):
    val = await db.get_setting_async(account_id, key)
    return {"key": key, "value": val}

@router.put("/")
async def update_setting(setting: SettingUpdate):
    success, msg = await db.set_setting_async(setting.account_id, setting.key, setting.value)
    if not success:
         raise HTTPException(status_code=500, detail=msg)
    return {"status": "success", "message": msg}
