"""
庫存服務
"""
import os
from typing import Optional, Tuple
from app.core.redis import get_redis_client


class InventoryService:
    """庫存服務類別"""
    
    @staticmethod
    def _get_stock_key(product_id: str) -> str:
        """取得庫存 Redis key"""
        return f"product:stock:{product_id}"
    
    @staticmethod
    def _load_lua_script() -> str:
        """載入庫存扣減 Lua 腳本"""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "scripts",
            "decrement_stock.lua"
        )
        
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # 如果檔案不存在，返回內嵌腳本
            return """
local product_key = KEYS[1]
local quantity = tonumber(ARGV[1])
local session_id = ARGV[2]

local current_stock = redis.call('GET', product_key)
if not current_stock then
    return {'err', 'PRODUCT_NOT_FOUND', 0}
end

current_stock = tonumber(current_stock)

if current_stock < quantity then
    return {'err', 'INSUFFICIENT_STOCK', current_stock}
end

local new_stock = current_stock - quantity
redis.call('SET', product_key, new_stock)

redis.call('SADD', 'purchases:' .. product_key, session_id)

return {'ok', true, new_stock}
"""
    
    @staticmethod
    def get_stock(product_id: str) -> int:
        """查詢庫存"""
        redis_client = get_redis_client()
        stock_key = InventoryService._get_stock_key(product_id)
        stock = redis_client.get(stock_key)
        return int(stock) if stock else 0
    
    @staticmethod
    def decrement_stock(product_id: str, quantity: int, session_id: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """扣減庫存（加入日誌）"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"使用者 {session_id} 嘗試購買商品 {product_id}，數量: {quantity}")
        """
        扣減庫存（使用 Lua 腳本確保原子性）
        
        Args:
            product_id: 商品 ID
            quantity: 購買數量
            session_id: 會話 ID
            
        Returns:
            Tuple[bool, Optional[str], Optional[int]]: (是否成功, 錯誤訊息, 剩餘庫存)
        """
        redis_client = get_redis_client()
        stock_key = InventoryService._get_stock_key(product_id)
        
        # 載入 Lua 腳本
        lua_script = InventoryService._load_lua_script()
        
        try:
            # 執行 Lua 腳本
            result = redis_client.eval(
                lua_script,
                1,  # KEYS 數量
                stock_key,  # KEYS[1]
                quantity,  # ARGV[1]
                session_id  # ARGV[2]
            )
            
            # Redis Lua 腳本返回的 table 會被轉換成列表
            # 格式：{ok = true, remaining_stock = 4} -> [True, 4] 或 [b'ok', True, 4]
            # 格式：{err = 'ERROR', stock = 0} -> [b'err', b'ERROR', 0]
            
            if isinstance(result, list) and len(result) > 0:
                # 檢查第一個元素
                first = result[0]
                
                # 處理字節串或字串
                if isinstance(first, bytes):
                    first = first.decode('utf-8')
                
                if first == "ok":
                    # 成功：{ok = true, remaining_stock = X} -> [True, X] 或 [b'ok', True, X]
                    if len(result) >= 3:
                        remaining_stock = result[2] if isinstance(result[2], int) else int(result[2])
                        return (True, None, remaining_stock)
                    elif len(result) >= 2:
                        # 可能是 [True, X] 格式
                        remaining_stock = result[1] if isinstance(result[1], int) else int(result[1])
                        return (True, None, remaining_stock)
                elif first == "err":
                    # 錯誤：{err = 'ERROR', stock = X} -> [b'err', b'ERROR', X]
                    error_msg = result[1].decode('utf-8') if isinstance(result[1], bytes) else str(result[1])
                    stock = result[2] if len(result) > 2 and result[2] is not None else None
                    return (False, error_msg, stock)
                elif first is True:
                    # 可能是 [True, remaining_stock] 格式
                    if len(result) >= 2:
                        remaining_stock = result[1] if isinstance(result[1], int) else int(result[1])
                        return (True, None, remaining_stock)
            
            # 如果無法解析，記錄並返回錯誤
            logger.error(f"無法解析 Lua 腳本返回結果: {result}, 類型: {type(result)}")
            return (False, "PARSE_ERROR", None)
            
        except Exception as e:
            logger.error(f"執行 Lua 腳本時發生錯誤: {str(e)}", exc_info=True)
            return (False, f"EXECUTION_ERROR: {str(e)}", None)
