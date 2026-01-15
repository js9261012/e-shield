-- 庫存扣減 Lua 腳本（原子操作）
local product_key = KEYS[1]
local quantity = tonumber(ARGV[1])
local session_id = ARGV[2]

-- 取得當前庫存
local current_stock = redis.call('GET', product_key)
if not current_stock then
    return {'err', 'PRODUCT_NOT_FOUND', 0}
end

current_stock = tonumber(current_stock)

-- 檢查庫存是否足夠
if current_stock < quantity then
    return {'err', 'INSUFFICIENT_STOCK', current_stock}
end

-- 扣減庫存
local new_stock = current_stock - quantity
redis.call('SET', product_key, new_stock)

-- 記錄購買（可選）
redis.call('SADD', 'purchases:' .. product_key, session_id)

-- 返回成功結果：['ok', true, remaining_stock]
return {'ok', true, new_stock}
