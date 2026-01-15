# 任務清單：反爬蟲排隊系統

## 憲章合規性檢查

- [x] 任務符合 MVP 原則：僅實作核心功能，避免過度設計
- [x] 每個任務都有明確的測試標準
- [x] 任務優先級明確（P0/P1/P2）
- [x] 任務描述使用正體中文

## 任務統計

- **總任務數**：58
- **Phase 1 (Setup)**：8 個任務
- **Phase 2 (Foundational)**：12 個任務
- **Phase 3 (US1: 正常使用者購買流程)**：15 個任務
- **Phase 4 (US2: 爬蟲阻擋)**：8 個任務
- **Phase 5 (US3: 查看排隊狀態)**：8 個任務
- **Phase 6 (Polish)**：7 個任務

## 依賴關係圖

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
Phase 3 (US1: 正常使用者購買流程) ← 核心功能
    ↓
Phase 4 (US2: 爬蟲阻擋)
    ↓
Phase 5 (US3: 查看排隊狀態)
    ↓
Phase 6 (Polish)
```

## 並行執行機會

- **Phase 2**: 多個服務/模型可以並行開發（標記 [P]）
- **Phase 3**: 前端和後端 API 可以並行開發（標記 [P]）
- **Phase 4**: Turnstile 前端和後端可以並行開發（標記 [P]）

## 實作策略

**MVP 範圍**：Phase 1 + Phase 2 + Phase 3（US1）
- 建立基礎架構
- 實作核心購買流程
- 可以進行基本展示

**增量交付**：
- 每個 Phase 完成後都可以獨立測試
- 每個 User Story 都是完整的功能增量

---

## Phase 1: 專案設定與基礎架構

**目標**：建立專案結構和 Docker 環境

### 基礎設施任務

- [x] T001 建立專案根目錄結構（backend/, frontend/, docker-compose.yml）
- [x] T002 建立 Docker Compose 配置檔案 docker-compose.yml（包含 FastAPI 和 Redis 服務）
- [x] T003 建立 FastAPI 後端專案結構 backend/（app/, tests/, requirements.txt）
- [x] T004 建立 Vue 前端專案結構 frontend/（src/, public/, package.json）
- [x] T005 建立後端 requirements.txt 並安裝依賴（fastapi, uvicorn, redis, httpx）
- [x] T006 建立前端 package.json 並安裝依賴（vue, axios, @cloudflare/turnstile）
- [x] T007 建立 .env.example 檔案，定義環境變數範本
- [x] T008 建立 .gitignore 檔案，排除不需要版本控制的檔案

**驗收標準**：
- `docker-compose up` 可以成功啟動所有服務
- 後端可以訪問 http://localhost:8000/docs
- 前端可以訪問 http://localhost:3000（如果配置了前端容器）

---

## Phase 2: 基礎功能與資料模型

**目標**：建立核心資料模型、Redis 連線和基礎服務

### Redis 連線與配置

- [ ] T009 建立 Redis 連線模組 backend/app/core/redis.py
- [ ] T010 建立 Redis 連線池配置，支援環境變數 REDIS_URL
- [ ] T011 建立 Redis 健康檢查端點 backend/app/api/health.py

### 資料模型

- [ ] T012 [P] 建立商品模型 backend/app/models/product.py（定義 Product 類別）
- [ ] T013 [P] 建立會話模型 backend/app/models/session.py（定義 Session 類別）
- [ ] T014 [P] 建立佇列模型 backend/app/models/queue.py（定義 QueueWaiting 和 QueueActive 類別）

### 基礎服務

- [ ] T015 建立商品服務 backend/app/services/product_service.py（初始化商品資料到 Redis）
- [ ] T016 建立會話服務 backend/app/services/session_service.py（建立、查詢、更新會話）
- [ ] T017 建立佇列服務 backend/app/services/queue_service.py（加入 waiting、查詢位置、移入 active）
- [ ] T018 建立庫存服務 backend/app/services/inventory_service.py（查詢庫存、使用 Lua 腳本扣減）

### Redis Lua 腳本

- [ ] T019 建立庫存扣減 Lua 腳本 backend/app/scripts/decrement_stock.lua
- [ ] T020 測試 Lua 腳本的原子性（確保不會超賣）

**驗收標準**：
- Redis 連線正常
- 商品資料可以初始化到 Redis
- 會話可以建立和查詢
- 佇列操作（加入 waiting、查詢位置）正常運作
- Lua 腳本可以正確扣減庫存

---

## Phase 3: User Story 1 - 正常使用者購買流程

**目標**：實作完整的購買流程，從查看商品到完成購買

### 獨立測試標準

- [ ] 使用者可以查看商品列表和詳情
- [ ] 使用者可以加入排隊（queue:waiting）
- [ ] 系統可以從 queue:waiting 移入 queue:active
- [ ] 使用者可以查詢佇列位置（waiting 和 active）
- [ ] 使用者輪到購買時（queue:active 位置 0）可以完成購買
- [ ] 購買後庫存正確扣減
- [ ] 購買完成後從 queue:active 移除並從 queue:waiting 補充新人

### 後端 API 實作

- [ ] T021 [US1] 實作商品列表 API backend/app/api/products.py（GET /api/products）
- [ ] T022 [US1] 實作商品詳情 API backend/app/api/products.py（GET /api/products/{product_id}）
- [ ] T023 [US1] 實作加入佇列 API backend/app/api/queue.py（POST /api/queue/join，加入 queue:waiting）
- [ ] T024 [US1] 實作佇列狀態查詢 API backend/app/api/queue.py（GET /api/queue/status）
- [ ] T025 [US1] 實作系統後台任務 backend/app/tasks/queue_manager.py（定期從 queue:waiting 移入 queue:active）
- [ ] T026 [US1] 實作購買 API backend/app/api/purchase.py（POST /api/purchase，只允許 queue:active 位置 0 的使用者）
- [ ] T027 [US1] 實作購買時限管理（5 分鐘超時檢查）
- [ ] T028 [US1] 實作購買完成後清理邏輯（從 queue:active 移除，從 queue:waiting 補充）

### 前端介面實作

- [ ] T029 [P] [US1] 建立商品列表頁面 frontend/src/views/ProductList.vue
- [ ] T030 [P] [US1] 建立商品詳情頁面 frontend/src/views/ProductDetail.vue
- [ ] T031 [P] [US1] 建立加入佇列頁面 frontend/src/views/JoinQueue.vue
- [ ] T032 [P] [US1] 建立佇列狀態頁面 frontend/src/views/QueueStatus.vue
- [ ] T033 [P] [US1] 建立購買確認頁面 frontend/src/views/Purchase.vue
- [ ] T034 [P] [US1] 建立購買結果頁面 frontend/src/views/PurchaseResult.vue
- [ ] T035 [US1] 建立 API 服務層 frontend/src/services/api.js（封裝所有 API 呼叫）

**驗收標準**：
- 所有 API 端點正常運作
- 前端可以完整執行購買流程
- 佇列順序正確（按時間排序）
- 庫存扣減準確，無超賣
- 購買時限管理正常

---

## Phase 4: User Story 2 - 爬蟲/機器人被阻擋

**目標**：實作 Turnstile 反爬蟲機制，阻擋自動化請求

### 獨立測試標準

- [ ] 正常使用者可以通過 Turnstile 驗證
- [ ] 未通過 Turnstile 驗證的請求無法加入佇列
- [ ] 缺少 Turnstile token 的請求被拒絕
- [ ] 無效的 Turnstile token 被拒絕

### Turnstile 整合

- [ ] T036 [P] [US2] 在前端整合 Turnstile widget frontend/src/components/TurnstileWidget.vue
- [ ] T037 [US2] 建立 Turnstile 驗證服務 backend/app/services/turnstile_service.py
- [ ] T038 [US2] 實作 Turnstile token 驗證邏輯（調用 Cloudflare API，使用測試模式金鑰）
- [ ] T039 [US2] 更新加入佇列 API，加入 Turnstile 驗證檢查 backend/app/api/queue.py
- [ ] T040 [US2] 實作速率限制中間件 backend/app/middleware/rate_limit.py（IP 基礎）

### 錯誤處理

- [ ] T041 [US2] 實作 Turnstile 驗證失敗的錯誤回應（403 錯誤）
- [ ] T042 [US2] 在前端顯示 Turnstile 驗證錯誤訊息
- [ ] T043 [US2] 實作基本爬蟲檢測（檢查 User-Agent、請求頻率）

**驗收標準**：
- Turnstile widget 正常顯示和運作（測試模式）
- 未通過驗證的請求無法加入佇列
- 錯誤訊息清晰明確
- 可以阻擋至少 80% 的簡單自動化請求

---

## Phase 5: User Story 3 - 查看排隊狀態

**目標**：實作即時佇列狀態更新和查詢功能

### 獨立測試標準

- [ ] 使用者可以查詢當前佇列位置（waiting 和 active）
- [ ] 佇列狀態可以即時更新（延遲 ≤ 5 秒）
- [ ] 使用者重新載入頁面後仍能查詢到正確的佇列狀態
- [ ] 前端可以顯示預估等待時間

### 即時更新實作

- [ ] T044 [US3] 實作 SSE 端點 backend/app/api/queue.py（GET /api/queue/stream）
- [ ] T045 [US3] 實作佇列狀態推送邏輯（定期推送位置更新）
- [ ] T046 [US3] 在前端整合 EventSource frontend/src/services/sse.js
- [ ] T047 [US3] 更新佇列狀態頁面，整合即時更新 frontend/src/views/QueueStatus.vue

### 狀態查詢優化

- [ ] T048 [US3] 優化佇列位置查詢 API（同時返回 waiting 和 active 位置）
- [ ] T049 [US3] 實作預估等待時間計算邏輯 backend/app/services/queue_service.py
- [ ] T050 [US3] 在前端顯示預估等待時間和佇列進度
- [ ] T051 [US3] 實作會話持久化（使用 LocalStorage 儲存 session_id）

**驗收標準**：
- 佇列狀態可以即時更新（SSE 正常運作）
- 位置查詢準確（waiting 和 active 位置正確）
- 預估等待時間合理
- 使用者體驗流暢

---

## Phase 6: 優化與完善

**目標**：完善錯誤處理、日誌、測試和文件

### 錯誤處理與日誌

- [x] T052 實作全域錯誤處理 middleware backend/app/middleware/error_handler.py
- [x] T053 實作結構化日誌記錄 backend/app/core/logging.py
- [x] T054 在所有關鍵操作中加入日誌記錄

### 測試

- [x] T055 撰寫單元測試 backend/tests/unit/（測試服務層邏輯，覆蓋率 ≥ 80%）
- [x] T056 撰寫整合測試 backend/tests/integration/（測試 API 端點和 Redis 互動）
- [ ] T057 撰寫端對端測試 frontend/tests/e2e/（測試完整購買流程）- 可選，需要 Playwright/Cypress

### 文件

- [x] T058 更新 README.md，包含專案說明、安裝步驟、使用指南（正體中文）

**驗收標準**：
- 錯誤處理完善，所有錯誤都有適當的錯誤訊息
- 日誌記錄完整，可以追蹤關鍵操作
- 測試覆蓋率達標（核心邏輯 ≥ 80%）
- 所有測試通過
- README 文件完整且清晰

---

## 驗收檢查清單

### Phase 1 驗收
- [ ] Docker Compose 可以成功啟動所有服務
- [ ] 專案結構完整

### Phase 2 驗收
- [ ] Redis 連線正常
- [ ] 所有資料模型和服務正常運作
- [ ] Lua 腳本測試通過

### Phase 3 驗收
- [ ] 完整購買流程可以執行
- [ ] 佇列順序正確
- [ ] 庫存管理準確

### Phase 4 驗收
- [ ] Turnstile 驗證正常運作
- [ ] 爬蟲請求被正確阻擋

### Phase 5 驗收
- [ ] 即時更新正常運作
- [ ] 佇列狀態查詢準確

### Phase 6 驗收
- [ ] 測試覆蓋率達標
- [ ] 錯誤處理完善
- [ ] 文件完整

### 整體驗收
- [ ] 所有功能需求（FR1-FR4）已實作
- [ ] 所有使用者場景可以完整執行
- [ ] 測試覆蓋率達標（核心邏輯 ≥ 80%）
- [ ] 程式碼通過靜態分析
- [ ] 文件完整且使用正體中文
- [ ] 符合憲章所有原則

---

## 並行執行範例

### Phase 2 並行執行
```bash
# 可以同時進行
- T012, T013, T014 (三個模型可以並行開發)
- T015, T016, T017, T018 (服務層可以並行開發)
```

### Phase 3 並行執行
```bash
# 前端和後端可以並行開發
後端：T021, T022, T023, T024, T025, T026, T027, T028
前端：T029, T030, T031, T032, T033, T034, T035
```

### Phase 4 並行執行
```bash
# Turnstile 前端和後端可以並行開發
前端：T036
後端：T037, T038, T039
```

---

## MVP 範圍建議

**最小可行產品 (MVP)**：Phase 1 + Phase 2 + Phase 3

**包含功能**：
- Docker Compose 環境
- 基礎架構和資料模型
- 完整購買流程（US1）
- 基本反爬蟲（Turnstile，但可以先簡化）

**不包含**：
- 即時更新（Phase 5）
- 完整爬蟲檢測（Phase 4 的部分功能）
- 完整測試覆蓋（Phase 6）

**MVP 驗收標準**：
- 可以進行基本展示
- 完整購買流程可以執行
- 系統穩定運行
