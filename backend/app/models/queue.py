"""
佇列模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class QueueStatus(BaseModel):
    """佇列狀態模型"""
    session_id: str = Field(..., description="會話 ID")
    queue_position_waiting: int = Field(..., description="在排隊區的位置（0-based，-1 表示不在排隊區）")
    queue_position_active: int = Field(..., description="在搖滾區的位置（0-based，-1 表示不在搖滾區，0 表示輪到購買）")
    total_in_waiting: int = Field(..., description="排隊區總人數")
    total_in_active: int = Field(..., description="搖滾區總人數（最多 100 人）")
    estimated_wait_time: int = Field(..., description="預估等待時間（秒）")
    status: str = Field(..., description="狀態：waiting, active, ready_to_purchase, purchased, expired")
    product_id: str = Field(..., description="商品 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123...",
                "queue_position_waiting": 500,
                "queue_position_active": -1,
                "total_in_waiting": 1000,
                "total_in_active": 100,
                "estimated_wait_time": 300,
                "status": "waiting",
                "product_id": "1"
            }
        }


class JoinQueueRequest(BaseModel):
    """加入佇列請求"""
    product_id: str = Field(..., description="商品 ID")
    turnstile_token: str = Field(..., description="Cloudflare Turnstile 驗證 token")


class JoinQueueResponse(BaseModel):
    """加入佇列回應"""
    success: bool = Field(..., description="是否成功")
    session_id: Optional[str] = Field(None, description="會話 ID（成功時）")
    queue_position_waiting: Optional[int] = Field(None, description="在排隊區的位置（成功時）")
    message: str = Field(..., description="訊息")
    error: Optional[str] = Field(None, description="錯誤代碼（失敗時）")
