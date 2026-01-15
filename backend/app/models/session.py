"""
會話模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Session(BaseModel):
    """會話資料模型"""
    session_id: str = Field(..., description="會話 ID")
    turnstile_verified: bool = Field(False, description="Turnstile 驗證狀態")
    verified_at: Optional[int] = Field(None, description="驗證時間戳（毫秒）")
    queue_position_waiting: Optional[int] = Field(None, description="在排隊區的位置")
    queue_position_active: Optional[int] = Field(-1, description="在搖滾區的位置（-1 表示不在搖滾區）")
    queue_status: str = Field("waiting", description="佇列狀態：waiting, active, ready_to_purchase, purchased, expired")
    product_id: Optional[str] = Field(None, description="加入的商品 ID")
    purchase_ready_at: Optional[int] = Field(None, description="可以購買的時間戳（毫秒）")
    purchase_timeout_at: Optional[int] = Field(None, description="購買時限過期時間戳（毫秒）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123...",
                "turnstile_verified": True,
                "verified_at": 1706342400000,
                "queue_position_waiting": 500,
                "queue_position_active": -1,
                "queue_status": "waiting",
                "product_id": "1"
            }
        }
