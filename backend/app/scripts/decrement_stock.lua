-- 庫存扣減 Lua 腳本（原子操作）
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
