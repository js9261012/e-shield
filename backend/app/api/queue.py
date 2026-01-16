"""
佇列 API
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.services.queue_service import QueueService
from app.services.session_service import SessionService
from app.services.turnstile_service import TurnstileService
from app.middleware.rate_limit import queue_rate_limiter
from app.models.queue import JoinQueueRequest, JoinQueueResponse, QueueStatus
import asyncio
import json

router = APIRouter()


@router.post("/queue/join", response_model=JoinQueueResponse)
async def join_queue(request: JoinQueueRequest, http_request: Request):
    """加入佇列（需通過 Turnstile 驗證）"""
    try:
        await queue_rate_limiter.check_rate_limit(http_request, "queue_join")
    except HTTPException:
        return JoinQueueResponse(
            success=False,
            error="RATE_LIMIT_EXCEEDED",
            message="請求過於頻繁，請稍後再試"
        )
    
    client_ip = http_request.client.host if http_request.client else None
    verified, error = await TurnstileService.verify_token(request.turnstile_token, client_ip)
    
    if not verified:
        return JoinQueueResponse(
            success=False,
            error="INVALID_TURNSTILE_TOKEN",
            message="Turnstile 驗證失敗，無法加入佇列"
        )
    
    session_id = SessionService.create_session(turnstile_verified=True)
    position = QueueService.join_waiting_queue(request.product_id, session_id)
    
    SessionService.update_session(
        session_id,
        product_id=request.product_id,
        queue_position_waiting=position,
        queue_status="waiting"
    )
    
    return JoinQueueResponse(
        success=True,
        session_id=session_id,
        queue_position_waiting=position,
        message="已成功加入排隊區"
    )


@router.get("/queue/status", response_model=QueueStatus)
async def get_queue_status(session_id: str, product_id: str):
    """查詢佇列狀態"""
    session = SessionService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="會話不存在")
    
    position_waiting = QueueService.get_waiting_position(product_id, session_id)
    position_active = QueueService.get_active_position(product_id, session_id)
    
    if position_waiting is None and position_active is None:
        raise HTTPException(status_code=404, detail="使用者不在佇列中")
    
    position_waiting = position_waiting if position_waiting is not None else -1
    position_active = position_active if position_active is not None else -1
    
    total_waiting = QueueService.get_waiting_count(product_id)
    total_active = QueueService.get_active_count(product_id)
    estimated_wait_time = QueueService.estimate_wait_time(
        product_id, position_waiting, position_active
    )
    
    if position_active >= 0:
        status = "ready_to_purchase"
    elif position_waiting >= 0:
        status = "waiting"
    else:
        status = "expired"
    
    return QueueStatus(
        session_id=session_id,
        queue_position_waiting=position_waiting,
        queue_position_active=position_active,
        total_in_waiting=total_waiting,
        total_in_active=total_active,
        estimated_wait_time=estimated_wait_time,
        status=status,
        product_id=product_id
    )


@router.get("/queue/stream")
async def stream_queue_status(session_id: str, product_id: str):
    """SSE 端點：即時推送佇列狀態更新"""
    async def event_generator():
        try:
            while True:
                position_waiting = QueueService.get_waiting_position(product_id, session_id)
                position_active = QueueService.get_active_position(product_id, session_id)
                
                if position_waiting is None and position_active is None:
                    yield f"event: queue_update\ndata: {json.dumps({'error': 'NOT_IN_QUEUE'})}\n\n"
                    break
                
                position_waiting = position_waiting if position_waiting is not None else -1
                position_active = position_active if position_active is not None else -1
                
                total_waiting = QueueService.get_waiting_count(product_id)
                total_active = QueueService.get_active_count(product_id)
                estimated_wait_time = QueueService.estimate_wait_time(
                    product_id, position_waiting, position_active
                )
                
                if position_active == 0:
                    status = "ready_to_purchase"
                elif position_active > 0:
                    status = "active"
                elif position_waiting >= 0:
                    status = "waiting"
                else:
                    status = "expired"
                
                data = {
                    "queue_position_waiting": position_waiting,
                    "queue_position_active": position_active,
                    "total_in_waiting": total_waiting,
                    "total_in_active": total_active,
                    "estimated_wait_time": estimated_wait_time,
                    "status": status
                }
                
                yield f"event: queue_update\ndata: {json.dumps(data)}\n\n"
                
                if status in ["ready_to_purchase", "purchased", "expired"]:
                    break
                
                await asyncio.sleep(3)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
