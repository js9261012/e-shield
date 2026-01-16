"""
購買 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.queue_service import QueueService
from app.services.inventory_service import InventoryService
from app.services.session_service import SessionService

router = APIRouter()


class PurchaseRequest(BaseModel):
    """購買請求"""
    product_id: str = Field(..., description="商品 ID")
    quantity: int = Field(1, description="購買數量（固定為 1）")
    session_id: str = Field(..., description="會話 ID")


class PurchaseResponse(BaseModel):
    """購買回應"""
    success: bool = Field(..., description="是否成功")
    order_id: Optional[str] = Field(None, description="訂單 ID（成功時）")
    product_id: Optional[str] = Field(None, description="商品 ID（成功時）")
    quantity: Optional[int] = Field(None, description="購買數量（成功時）")
    remaining_stock: Optional[int] = Field(None, description="剩餘庫存（成功時）")
    message: str = Field(..., description="訊息")
    error: Optional[str] = Field(None, description="錯誤代碼（失敗時）")


@router.post("/purchase", response_model=PurchaseResponse)
async def purchase(request: PurchaseRequest):
    """處理購買（僅搖滾區使用者可購買）"""
    session = SessionService.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    position_active = QueueService.get_active_position(request.product_id, request.session_id)
    
    if position_active is None:
        return PurchaseResponse(
            success=False,
            error="NOT_IN_ACTIVE_QUEUE",
            message="您不在搖滾區，無法購買"
        )
    
    if request.quantity != 1:
        return PurchaseResponse(
            success=False,
            error="INVALID_REQUEST",
            message="每人限購 1 雙"
        )
    
    success, error, remaining_stock = InventoryService.decrement_stock(
        request.product_id,
        request.quantity,
        request.session_id
    )
    
    if not success:
        if error == "INSUFFICIENT_STOCK":
            return PurchaseResponse(
                success=False,
                error="INSUFFICIENT_STOCK",
                message="庫存不足"
            )
        elif error == "PRODUCT_NOT_FOUND":
            return PurchaseResponse(
                success=False,
                error="PRODUCT_NOT_FOUND",
                message="商品不存在"
            )
        else:
            return PurchaseResponse(
                success=False,
                error=error or "UNKNOWN_ERROR",
                message="購買失敗"
            )
    
    QueueService.remove_from_active(request.product_id, request.session_id)
    SessionService.update_session(
        request.session_id,
        queue_status="purchased"
    )
    QueueService.move_to_active(request.product_id)
    
    import uuid
    order_id = f"order_{uuid.uuid4().hex[:8]}"
    
    return PurchaseResponse(
        success=True,
        order_id=order_id,
        product_id=request.product_id,
        quantity=request.quantity,
        remaining_stock=remaining_stock,
        message="購買成功"
    )
