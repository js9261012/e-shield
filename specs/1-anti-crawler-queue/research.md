# 技術研究與決策文件

**功能**：反爬蟲排隊系統  
**日期**：2025-01-27  
**目的**：記錄技術選型和實作決策

## 研究項目

### 1. Cloudflare Turnstile 整合（Demo 模式）

**研究問題**：如何在 demo 環境中使用 Turnstile 進行反爬蟲驗證？

**決策**：使用 Turnstile 的測試模式（test mode）

**理由**：
- Turnstile 提供測試模式，無需真實金鑰即可驗證整合流程
- 測試模式的行為與生產模式相同，適合展示
- 前端 widget 和後端驗證 API 都可以使用測試模式

**實作方式**：
- 前端：使用 Turnstile widget，設定 `sitekey` 為測試金鑰
- 後端：使用 Turnstile 驗證 API，設定 `secret` 為測試金鑰
- 測試模式金鑰：
  - Site key: `1x00000000000000000000AA`
  - Secret key: `1x0000000000000000000000000000000AA`

**重要流程**：
- **Turnstile 驗證是加入 Redis 佇列的前置條件**
- 使用者必須先在前端完成 Turnstile widget 驗證，獲得 token
- 後端在處理 `POST /api/queue/join` 請求時，先驗證 Turnstile token
- 驗證成功 → 允許加入 Redis 佇列
- 驗證失敗 → 返回 403 錯誤，**不會加入佇列**

**替代方案考慮**：
- **reCAPTCHA**：需要 Google 帳號，測試較複雜
- **hCaptcha**：功能類似，但 Turnstile 更現代且無障礙性更好
- **自建驗證碼**：開發成本高，不符合 MVP 原則

**參考資源**：
- [Cloudflare Turnstile 文件](https://developers.cloudflare.com/turnstile/)
- [Turnstile 測試模式](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/)

---

### 2. Redis 兩階段佇列實作模式

**研究問題**：如何在高併發場景下使用 Redis 實作公平的排隊系統，並控制同時購買的人數？

**決策**：使用兩個 Redis Sorted Set 實作兩階段佇列系統

**理由**：
- **兩階段設計**：可以控制同時進行購買的人數，避免系統過載
- **排隊區（queue:waiting）**：容納幾萬人等待，通過 Turnstile 驗證後先進入此區
- **搖滾區（queue:active）**：只有被系統允許的人（例如 100 人）會在這裡，只有此區的人才能購買
- Sorted Set 自動排序，確保順序
- 支援原子操作（ZADD, ZRANK, ZREM）
- 高效能，適合高併發場景
- 可以輕鬆查詢位置和範圍

**實作方式**：

**排隊區（queue:waiting）**：
- Key 格式：`queue:waiting:product:{product_id}`
- Member：使用者會話 ID（session_id）
- Score：加入時間戳（毫秒級）
- 用途：通過 Turnstile 驗證的使用者先進入此區等待，可能有幾萬人
- 操作：
  - 加入：`ZADD queue:waiting:product:1 {timestamp} {session_id}`
  - 查詢位置：`ZRANK queue:waiting:product:1 {session_id}`
  - 取得前方人數：`ZCOUNT queue:waiting:product:1 -inf {current_score}`
  - 取得前 N 個（移入搖滾區）：`ZRANGE queue:waiting:product:1 0 {N-1} WITHSCORES`
  - 移除：`ZREM queue:waiting:product:1 {session_id}`

**搖滾區（queue:active）**：
- Key 格式：`queue:active:product:{product_id}`
- Member：使用者會話 ID（session_id）
- Score：進入搖滾區的時間戳（毫秒級）
- 用途：只有被系統允許的人（例如 100 人）會在這裡，只有此區的人才能購買
- 容量限制：系統設定最大容量（例如 100 人），當有人購買完成或超時離開時，從 `queue:waiting` 中補充新人
- 操作：
  - 從排隊區移入：`ZADD queue:active:product:1 {timestamp} {session_id}`（同時從 waiting 移除）
  - 查詢位置：`ZRANK queue:active:product:1 {session_id}`（0 表示輪到購買）
  - 取得當前可購買的人：`ZRANGE queue:active:product:1 0 0 WITHSCORES`
  - 移除（購買完成或超時）：`ZREM queue:active:product:1 {session_id}`

**流程**：
1. 通過 Turnstile 驗證 → 加入 `queue:waiting`
2. 系統後台定期從 `queue:waiting` 中選取一定數量的人（例如 100 人）移入 `queue:active`
3. 只有 `queue:active` 中的人才能進行購買
4. 當 `queue:active` 中有人購買完成或超時離開時，從 `queue:waiting` 中補充新人

**替代方案考慮**：
- **單一佇列**：無法控制同時購買的人數，可能導致系統過載
- **Redis List (LPUSH/RPOP)**：簡單但查詢位置需要遍歷，效能較差
- **Redis Stream**：功能強大但過於複雜，不符合 MVP 原則
- **資料庫佇列**：效能較差，不適合高併發

**參考資源**：
- [Redis Sorted Sets 文件](https://redis.io/docs/data-types/sorted-sets/)
- [Redis 佇列模式](https://redis.io/docs/manual/patterns/queue/)

---

### 3. Redis Lua 腳本庫存控制

**研究問題**：如何確保庫存扣減的原子性，避免超賣？

**決策**：使用 Redis Lua 腳本實作原子庫存扣減

**理由**：
- Lua 腳本在 Redis 中原子執行，確保一致性
- 可以檢查庫存、扣減庫存、記錄訂單在同一個原子操作中完成
- 高效能，避免網路往返

**實作方式**：
```lua
-- 庫存扣減 Lua 腳本
local product_key = KEYS[1]
local quantity = tonumber(ARGV[1])
local session_id = ARGV[2]

-- 取得當前庫存
local current_stock = redis.call('GET', product_key)
if not current_stock then
    return {err = 'PRODUCT_NOT_FOUND'}
end

current_stock = tonumber(current_stock)

-- 檢查庫存是否足夠
if current_stock < quantity then
    return {err = 'INSUFFICIENT_STOCK', stock = current_stock}
end

-- 扣減庫存
local new_stock = current_stock - quantity
redis.call('SET', product_key, new_stock)

-- 記錄購買（可選）
redis.call('SADD', 'purchases:' .. product_key, session_id)

return {ok = true, remaining_stock = new_stock}
```

**替代方案考慮**：
- **Redis WATCH/MULTI/EXEC**：需要重試邏輯，較複雜
- **資料庫事務**：效能較差，不適合高併發
- **分散式鎖**：過於複雜，不符合 MVP 原則

**參考資源**：
- [Redis Lua 腳本文件](https://redis.io/docs/manual/programmability/eval-intro/)
- [Redis 原子操作模式](https://redis.io/docs/manual/patterns/atomic-operations/)

---

### 4. 即時更新機制（WebSocket vs SSE）

**研究問題**：如何實現佇列狀態的即時更新？

**決策**：使用 Server-Sent Events (SSE)

**理由**：
- SSE 實作簡單，FastAPI 原生支援
- 單向推送適合佇列狀態更新場景
- 自動重連機制，使用者體驗好
- 比 WebSocket 更輕量，符合 MVP 原則

**實作方式**：
- FastAPI 使用 `StreamingResponse` 實作 SSE
- 前端使用 `EventSource` API 接收更新
- 更新頻率：每 2-3 秒推送一次佇列狀態

**替代方案考慮**：
- **WebSocket**：雙向通訊，但此場景不需要，過於複雜
- **輪詢 (Polling)**：簡單但效率低，不符合即時更新要求
- **Long Polling**：實作複雜，不如 SSE 優雅

**參考資源**：
- [FastAPI SSE 範例](https://fastapi.tiangolo.com/advanced/server-sent-events/)
- [MDN EventSource 文件](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)

---

### 5. 會話管理策略

**研究問題**：如何識別和追蹤使用者（無帳號系統）？

**決策**：使用 Redis 儲存會話，session ID 由後端生成

**理由**：
- 簡單有效，符合 MVP 原則
- Redis 高效能，適合會話儲存
- 可以設定過期時間，自動清理

**實作方式**：
- 後端生成 UUID 作為 session_id
- 儲存在 Redis：`session:{session_id}` -> `{turnstile_verified: true, queue_position: 10, ...}`
- 前端使用 Cookie 或 LocalStorage 儲存 session_id
- 會話過期時間：24 小時

**替代方案考慮**：
- **JWT Token**：需要簽名驗證，過於複雜
- **資料庫會話表**：效能較差，不符合 MVP 原則

**參考資源**：
- [Redis 會話管理模式](https://redis.io/docs/manual/patterns/session-management/)

---

### 6. Docker Compose 架構設計

**研究問題**：如何組織 Docker Compose 服務和網路？

**決策**：使用兩個容器（FastAPI + Redis），共用網路

**理由**：
- 簡單清晰，符合 MVP 原則
- 易於部署和測試
- 未來可以輕鬆擴展（加入前端容器、資料庫等）

**實作方式**：
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  fastapi:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
```

**替代方案考慮**：
- **單一容器（所有服務）**：不符合容器化最佳實踐
- **Kubernetes**：過於複雜，不符合 MVP 原則

**參考資源**：
- [Docker Compose 文件](https://docs.docker.com/compose/)

---

## 技術決策總結

| 決策項目 | 選擇 | 理由 |
|---------|------|------|
| 反爬蟲服務 | Cloudflare Turnstile (測試模式) | 簡單、現代、適合展示 |
| 佇列儲存 | Redis Sorted Set | 高效能、自動排序、原子操作 |
| 庫存控制 | Redis Lua 腳本 | 原子性、高效能、避免超賣 |
| 即時更新 | Server-Sent Events (SSE) | 簡單、單向推送、自動重連 |
| 會話管理 | Redis 會話儲存 | 簡單、高效能、自動過期 |
| 容器化 | Docker Compose (2 容器) | 簡單、易部署、易擴展 |

## 已知限制與風險

1. **Redis 單點故障**：MVP 階段接受，未來可加入高可用性配置
2. **Turnstile 測試模式**：僅用於展示，不適用於生產環境
3. **會話儲存**：無持久化，重啟 Redis 會丟失會話（MVP 階段可接受）
4. **無負載平衡**：單一 FastAPI 實例，未來可加入負載平衡器

## 後續研究項目（未來迭代）

- Redis Cluster 或 Sentinel 高可用性配置
- 資料持久化策略（PostgreSQL/MySQL）
- 進階反爬蟲技術（機器學習、行為分析）
- 微服務架構拆分
- 監控和日誌聚合（Prometheus, Grafana）
