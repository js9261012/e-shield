# 資料模型定義

**功能**：反爬蟲排隊系統  
**日期**：2025-01-27

## 概述

本文件定義系統中使用的所有資料模型，包括 Redis 資料結構、API 請求/回應格式等。

## Redis 資料結構

### 1. 商品庫存 (Product Stock)

**Key 格式**：`product:stock:{product_id}`

**類型**：String (整數)

**值**：剩餘庫存數量（整數）

**範例**：
```
product:stock:1 -> "5"
product:stock:2 -> "3"
```

**操作**：
- 初始化：`SET product:stock:1 5`
- 查詢：`GET product:stock:1`
- 扣減：使用 Lua 腳本（見下方）

---

### 2. 排隊區 (Queue Waiting)

**Key 格式**：`queue:waiting:product:{product_id}`

**類型**：Sorted Set

**Member**：使用者會話 ID (session_id)

**Score**：加入時間戳（毫秒，Unix timestamp）

**用途**：通過 Turnstile 驗證的使用者先進入此區等待，可能有幾萬人在此等待。這是第一階段排隊，使用者在此等待被系統選入搖滾區。

**範例**：
```
queue:waiting:product:1 -> {
  "session_abc123": 1706342400000,
  "session_def456": 1706342401000,
  "session_ghi789": 1706342402000,
  ... (可能有幾萬人)
}
```

**操作**：
- 加入排隊區：`ZADD queue:waiting:product:1 {timestamp} {session_id}`
- 查詢位置：`ZRANK queue:waiting:product:1 {session_id}`（返回 0-based 位置）
- 查詢前方人數：`ZCOUNT queue:waiting:product:1 -inf {current_score}`
- 取得排隊區長度：`ZCARD queue:waiting:product:1`
- 移除：`ZREM queue:waiting:product:1 {session_id}`
- 取得前 N 個（用於移入搖滾區）：`ZRANGE queue:waiting:product:1 0 {N-1} WITHSCORES`

---

### 3. 搖滾區/白名單 (Queue Active)

**Key 格式**：`queue:active:product:{product_id}`

**類型**：Sorted Set

**Member**：使用者會話 ID (session_id)

**Score**：進入搖滾區的時間戳（毫秒，Unix timestamp）

**用途**：只有被系統允許的人（例如 100 人）會在這裡，只有此區的人才能進行購買。這是第二階段排隊（搖滾區/白名單），系統會從 `queue:waiting` 中按順序選取使用者移入此區。

**容量限制**：系統設定最大容量（例如 100 人），當有人購買完成或超時離開時，從 `queue:waiting` 中按順序補充新人，保持搖滾區滿員狀態。

**運作邏輯**：
1. 系統定期檢查 `queue:active` 的當前人數
2. 如果人數少於最大容量（例如 100 人），從 `queue:waiting` 中選取最前面的使用者移入
3. 移入時，同時從 `queue:waiting` 中移除該使用者
4. 只有 `queue:active` 中位置為 0 的使用者才能進行購買
5. 購買完成或超時後，從 `queue:active` 中移除，並從 `queue:waiting` 補充新人

**範例**：
```
queue:active:product:1 -> {
  "session_xyz111": 1706342500000,
  "session_xyz222": 1706342501000,
  ... (最多 100 人)
}
```

**操作**：
- 從排隊區移入搖滾區：`ZADD queue:active:product:1 {timestamp} {session_id}`（同時從 waiting 移除）
- 查詢位置：`ZRANK queue:active:product:1 {session_id}`（返回 0-based 位置，0 表示輪到購買）
- 查詢前方人數：`ZCOUNT queue:active:product:1 -inf {current_score}`
- 取得搖滾區長度：`ZCARD queue:active:product:1`
- 取得當前可購買的人（位置 0）：`ZRANGE queue:active:product:1 0 0 WITHSCORES`
- 移除（購買完成或超時）：`ZREM queue:active:product:1 {session_id}`

---

### 4. 會話 (Session)

**Key 格式**：`session:{session_id}`

**類型**：Hash

**欄位**：
- `turnstile_verified`: 布林值（"true" 或 "false"）
- `verified_at`: 驗證時間戳（毫秒）
- `queue_position_waiting`: 在排隊區的位置（整數，可選）
- `queue_position_active`: 在搖滾區的位置（整數，可選，-1 表示不在搖滾區）
- `queue_status`: 佇列狀態（"waiting", "active", "ready_to_purchase", "purchased", "expired"）
- `product_id`: 加入的商品 ID（字串，可選）
- `purchase_ready_at`: 可以購買的時間戳（毫秒，可選）
- `purchase_timeout_at`: 購買時限過期時間戳（毫秒，可選）

**範例**：
```
session:abc123 -> {
  "turnstile_verified": "true",
  "verified_at": "1706342400000",
  "queue_position_waiting": "500",
  "queue_position_active": "-1",
  "queue_status": "waiting",
  "product_id": "1",
  "purchase_ready_at": "1706342500000",
  "purchase_timeout_at": "1706342800000"
}
```

**操作**：
- 建立會話：`HSET session:abc123 turnstile_verified true verified_at 1706342400000`
- 查詢會話：`HGETALL session:abc123`
- 更新位置：`HSET session:abc123 queue_position_waiting 500 queue_status waiting`
- 移入搖滾區：`HSET session:abc123 queue_position_active 10 queue_status active`
- 設定過期：`EXPIRE session:abc123 86400`（24 小時）

---

### 5. 購買記錄 (Purchase Record)

**Key 格式**：`purchases:product:{product_id}`

**類型**：Set

**Member**：使用者會話 ID (session_id)

**用途**：記錄已購買的使用者（用於統計和防重複購買）

**範例**：
```
purchases:product:1 -> {
  "session_abc123",
  "session_def456"
}
```

**操作**：
- 記錄購買：`SADD purchases:product:1 session_abc123`
- 檢查是否已購買：`SISMEMBER purchases:product:1 session_abc123`
- 取得購買數量：`SCARD purchases:product:1`

---

### 6. 購買時限鎖 (Purchase Timeout Lock)

**Key 格式**：`purchase:lock:{session_id}`

**類型**：String (時間戳)

**值**：購買時限過期時間戳（毫秒）

**用途**：追蹤使用者購買時限，用於自動清理

**範例**：
```
purchase:lock:abc123 -> "1706342800000"
```

**操作**：
- 設定鎖：`SET purchase:lock:abc123 1706342800000 EX 300`（5 分鐘過期）
- 檢查是否過期：比較當前時間與鎖的值
- 自動過期：使用 Redis EXPIRE 自動清理

---

## API 資料模型

### 商品 (Product)

**回應格式**：
```json
{
  "id": "1",
  "name": "限量球鞋 A",
  "image_url": "https://example.com/shoe-a.jpg",
  "price": 9999,
  "total_stock": 5,
  "remaining_stock": 3
}
```

**欄位說明**：
- `id` (string, required): 商品 ID
- `name` (string, required): 商品名稱
- `image_url` (string, required): 商品圖片 URL
- `price` (integer, required): 價格（分）
- `total_stock` (integer, required): 總庫存
- `remaining_stock` (integer, required): 剩餘庫存

---

### 加入佇列請求 (Join Queue Request)

**重要流程說明**：
1. **必須先通過 Turnstile 驗證**：使用者在前端完成 Turnstile widget 驗證，獲得 token
2. **驗證通過後才能加入佇列**：後端驗證 Turnstile token，驗證成功後才將使用者加入 Redis 佇列
3. **驗證失敗無法加入**：如果 Turnstile token 驗證失敗，請求會被拒絕，不會加入佇列

**請求格式**：
```json
{
  "product_id": "1",
  "turnstile_token": "0.abc123..."
}
```

**欄位說明**：
- `product_id` (string, required): 商品 ID
- `turnstile_token` (string, required): Cloudflare Turnstile 驗證 token（必須是有效的驗證 token）

**驗證流程**：
1. 前端：使用者完成 Turnstile widget → 獲得 token
2. 前端：發送 `POST /api/queue/join` 請求，包含 `turnstile_token`
3. 後端：驗證 Turnstile token（調用 Cloudflare API）
4. 後端：如果驗證成功 → 建立會話 → **加入 `queue:waiting`（排隊區）**
5. 後端：如果驗證失敗 → 返回錯誤，不加入佇列
6. **系統後台**：定期從 `queue:waiting` 中選取一定數量的人（例如 100 人）移入 `queue:active`（搖滾區）
7. **只有 `queue:active` 中的人才能進行購買**

---

### 加入佇列回應 (Join Queue Response)

**成功回應**：
```json
{
  "success": true,
  "session_id": "abc123...",
  "queue_position_waiting": 500,
  "queue_status": "waiting",
  "message": "已成功加入排隊區"
}
```

**欄位說明**：
- `queue_position_waiting`: 在排隊區的位置（0-based）
- `queue_status`: 佇列狀態（"waiting" 表示在排隊區等待進入搖滾區）

**錯誤回應**：
```json
{
  "success": false,
  "error": "INVALID_TURNSTILE_TOKEN",
  "message": "Turnstile 驗證失敗，無法加入佇列"
}
```

**錯誤情況**：
- `INVALID_TURNSTILE_TOKEN`: Turnstile token 驗證失敗，**不會加入佇列**
- `PRODUCT_NOT_FOUND`: 商品不存在
- `ALREADY_IN_QUEUE`: 使用者已經在佇列中

**欄位說明**：
- `success` (boolean, required): 是否成功
- `session_id` (string, optional): 會話 ID（成功時）
- `queue_position_waiting` (integer, optional): 在排隊區的位置（成功時）
- `queue_status` (string, optional): 佇列狀態（成功時）
- `error` (string, optional): 錯誤代碼（失敗時）
- `message` (string, required): 訊息

---

### 佇列狀態 (Queue Status)

**回應格式**：
```json
{
  "session_id": "abc123...",
  "queue_status": "waiting",
  "queue_position_waiting": 500,
  "queue_position_active": -1,
  "total_in_waiting": 5000,
  "total_in_active": 100,
  "estimated_wait_time": 300,
  "product_id": "1"
}
```

**欄位說明**：
- `session_id` (string, required): 會話 ID
- `queue_status` (string, required): 佇列狀態（"waiting", "active", "ready_to_purchase", "purchased", "expired"）
- `queue_position_waiting` (integer, required): 在排隊區的位置（0-based，-1 表示不在排隊區）
- `queue_position_active` (integer, required): 在搖滾區的位置（0-based，-1 表示不在搖滾區，0 表示輪到購買）
- `total_in_waiting` (integer, required): 排隊區總人數
- `total_in_active` (integer, required): 搖滾區總人數（最多 100 人）
- `estimated_wait_time` (integer, required): 預估等待時間（秒）
- `product_id` (string, required): 商品 ID

**狀態說明**：
- `waiting`: 在排隊區等待進入搖滾區
- `active`: 在搖滾區等待輪到購買
- `ready_to_purchase`: 可以購買（queue_position_active = 0）
- `purchased`: 已購買
- `expired`: 已過期（購買時限過期或會話過期）

---

### 購買請求 (Purchase Request)

**請求格式**：
```json
{
  "product_id": "1",
  "quantity": 1
}
```

**欄位說明**：
- `product_id` (string, required): 商品 ID
- `quantity` (integer, required): 購買數量（1-1，每人限購 1 雙）

---

### 購買回應 (Purchase Response)

**成功回應**：
```json
{
  "success": true,
  "order_id": "order_abc123...",
  "product_id": "1",
  "quantity": 1,
  "remaining_stock": 2,
  "message": "購買成功"
}
```

**錯誤回應**：
```json
{
  "success": false,
  "error": "INSUFFICIENT_STOCK",
  "message": "庫存不足"
}
```

**欄位說明**：
- `success` (boolean, required): 是否成功
- `order_id` (string, optional): 訂單 ID（成功時）
- `product_id` (string, optional): 商品 ID（成功時）
- `quantity` (integer, optional): 購買數量（成功時）
- `remaining_stock` (integer, optional): 剩餘庫存（成功時）
- `error` (string, optional): 錯誤代碼（失敗時）
- `message` (string, required): 訊息

**錯誤代碼**：
- `NOT_IN_QUEUE`: 使用者不在佇列中（既不在 waiting 也不在 active）
- `NOT_IN_ACTIVE`: 使用者不在搖滾區，無法購買
- `NOT_READY`: 尚未輪到使用者（queue_position_active != 0）
- `TIMEOUT`: 購買時限已過
- `INSUFFICIENT_STOCK`: 庫存不足
- `ALREADY_PURCHASED`: 已經購買過
- `INVALID_REQUEST`: 無效請求

---

## 驗證規則

### 商品 ID
- 必須為非空字串
- 格式：數字字串（如 "1", "2"）

### 會話 ID
- 必須為 UUID 格式
- 長度：36 字元（包含連字號）

### 購買數量
- 必須為整數
- 範圍：1-1（每人限購 1 雙）
- MVP 階段固定為 1

### 時間戳
- 格式：Unix 時間戳（毫秒）
- 類型：整數

---

## 資料一致性保證

### 庫存扣減原子性
- 使用 Redis Lua 腳本確保檢查庫存和扣減庫存的原子性
- 腳本執行期間，其他請求會等待

### 佇列順序保證
- 使用 Redis Sorted Set 自動排序
- Score 使用毫秒級時間戳，確保順序準確

### 會話一致性
- 會話資料使用 Redis Hash 儲存
- 使用 EXPIRE 設定過期時間，自動清理

---

## 資料過期策略

| 資料類型 | 過期時間 | 理由 |
|---------|---------|------|
| 會話 (Session) | 24 小時 | 使用者可能長時間等待 |
| 購買時限鎖 | 5 分鐘 | 購買時限 |
| 佇列資料 | 不設定過期 | 手動清理（商品售完後） |
| 購買記錄 | 不設定過期 | 用於統計，長期保存 |

---

## 未來擴展考慮

- 商品資訊可以從 Redis 遷移到資料庫
- 訂單記錄可以持久化到資料庫
- 可以加入商品快取機制
- 可以加入統計資料（購買率、平均等待時間等）
