# 功能規劃：反爬蟲排隊系統

## 憲章合規性檢查

- [x] 符合 MVP 原則：僅實作核心反爬蟲機制和基本排隊功能，使用 Docker Compose 簡化部署
- [x] 可測試性：已規劃測試策略，包含單元測試、整合測試和端對端測試
- [x] 品質標準：已考慮程式碼品質要求，使用靜態分析工具
- [x] 正體中文：文件使用正體中文撰寫
- [x] 漸進式開發：功能可拆分為多個迭代階段

## 功能概述

建立一個可展示的反爬蟲排隊系統，用於搶購稀有球鞋場景。系統使用 Cloudflare Turnstile 進行應用層機器人防護，Redis 處理高併發排隊，並使用 Lua 腳本確保庫存控制的原子性。系統採用 Docker Compose 打包，包含 FastAPI 後端和 Vue 前端，適合快速部署和展示。

## 技術上下文

### 技術棧選擇

**後端框架**：FastAPI
- **理由**：現代化的 Python Web 框架，自動生成 OpenAPI 文件，高效能，適合快速開發
- **版本**：Python 3.11+, FastAPI 0.104+

**前端框架**：Vue 3
- **理由**：輕量級、易於學習，適合快速建立展示介面
- **版本**：Vue 3.x

**資料儲存與佇列**：Redis
- **理由**：高效能記憶體資料庫，支援原子操作和 Lua 腳本，適合高併發排隊場景
- **版本**：Redis 7.x
- **用途**：
  - 佇列管理（使用 List 或 Sorted Set）
  - 庫存控制（使用 Lua 腳本確保原子性）
  - 會話儲存（session storage）
  - 速率限制（rate limiting）

**反爬蟲服務**：Cloudflare Turnstile
- **理由**：應用層機器人防護，無需使用者互動，適合展示場景
- **實作方式**：使用假金鑰（demo 模式），僅用於展示流程
- **整合方式**：前端嵌入 Turnstile widget，後端驗證 token

**容器化**：Docker Compose
- **理由**：簡化部署，一鍵啟動所有服務
- **容器**：
  - `fastapi`: FastAPI 後端服務
  - `redis`: Redis 資料庫

### 架構設計

```
┌─────────────┐
│   Vue 前端   │
│  (靜態檔案)   │
└──────┬──────┘
       │ HTTP/WebSocket
       ▼
┌─────────────┐      ┌─────────────┐
│  FastAPI    │◄────►│    Redis    │
│   後端      │      │  (佇列+庫存) │
└──────┬──────┘      └─────────────┘
       │
       │ Turnstile 驗證
       ▼
┌─────────────┐
│ Cloudflare  │
│  Turnstile  │
└─────────────┘
```

### 核心技術決策

1. **兩階段佇列實作**：
   - `queue:waiting`（排隊區）：通過 Turnstile 驗證的使用者先進入此區，可能有幾萬人在此等待
   - `queue:active`（搖滾區/白名單）：系統從 `queue:waiting` 中選取一定數量的人（例如 100 人）進入此區
   - 只有 `queue:active` 中的人才能進行購買
   - 使用 Redis Sorted Set 儲存兩個佇列，score 為進入時間戳，確保順序
2. **庫存控制**：使用 Redis Lua 腳本確保庫存扣減的原子性，避免超賣
3. **會話管理**：使用 Redis 儲存使用者會話，識別使用者身份
4. **即時更新**：使用 WebSocket 或 Server-Sent Events (SSE) 推送佇列狀態更新
5. **反爬蟲流程**：**必須先通過 Turnstile 驗證** → 驗證通過後進入 `queue:waiting` → 系統選取進入 `queue:active` → 等待 → 購買
   - 重要：Turnstile 驗證是加入佇列的前置條件，未通過驗證的請求無法加入佇列

## 範圍界定

### 包含範圍

- **反爬蟲機制**：
  - Cloudflare Turnstile 整合（使用假金鑰）
  - **Turnstile 驗證是加入佇列的前置條件**：必須先通過驗證才能加入 Redis 佇列
  - 基本的速率限制（IP 基礎）
  - 會話驗證

- **兩階段排隊系統**：
  - `queue:waiting`（排隊區）：通過 Turnstile 驗證的使用者先進入此區等待，可能有幾萬人在此等待
  - `queue:active`（搖滾區/白名單）：系統從 `queue:waiting` 中選取一定數量的人（例如 100 人）進入此區
  - 只有 `queue:active` 中的人才能進行購買
  - 系統後台定期檢查 `queue:active` 容量，從 `queue:waiting` 中按順序補充新人
  - 佇列位置查詢（分別查詢在 waiting 和 active 中的位置）
  - 佇列狀態即時更新（WebSocket/SSE）
  - 購買時限管理（5 分鐘）

- **庫存管理**：
  - Redis Lua 腳本實作的原子庫存扣減
  - 庫存查詢
  - 超賣防護

- **使用者介面**：
  - 商品展示頁面
  - 排隊狀態頁面
  - 購買確認頁面
  - 結果顯示頁面

- **API 端點**：
  - 商品資訊查詢
  - 加入佇列
  - 查詢佇列位置
  - 購買處理
  - WebSocket/SSE 端點（佇列狀態推送）

- **部署**：
  - Docker Compose 配置
  - 環境變數配置
  - 基本錯誤處理和日誌

### 不包含範圍（未來迭代）

- 使用者帳號系統和認證
- 真實的支付整合
- 訂單管理和歷史記錄
- 管理後台
- 進階的反爬蟲技術（機器學習、行為分析）
- 多商品支援
- 通知系統（Email、簡訊）
- 資料持久化（PostgreSQL/MySQL）
- 負載平衡和高可用性配置

## 測試策略

### 單元測試

- **FastAPI 路由測試**：
  - 使用 `TestClient` 測試所有 API 端點
  - 測試請求驗證、錯誤處理
  - 測試覆蓋率目標：≥ 80%

- **業務邏輯測試**：
  - 佇列管理邏輯
  - 庫存計算邏輯
  - 會話管理邏輯

- **Redis Lua 腳本測試**：
  - 測試庫存扣減腳本
  - 測試併發場景下的原子性

### 整合測試

- **FastAPI + Redis 整合**：
  - 測試完整的購買流程
  - 測試佇列順序正確性
  - 測試庫存管理準確性

- **Turnstile 整合測試**：
  - 模擬 Turnstile 驗證流程
  - 測試驗證失敗場景

- **WebSocket/SSE 測試**：
  - 測試佇列狀態即時更新

### 端對端測試

- **完整使用者流程**：
  - 使用 Playwright 或 Cypress 測試完整購買流程
  - 測試多使用者並發場景
  - 測試爬蟲阻擋場景

### 測試覆蓋率目標

- 核心邏輯（佇列、庫存、購買）：≥ 80%
- API 端點：100%
- 整體覆蓋率：≥ 70%

## 實作計劃

### 階段 0：研究與設計（Phase 0）

**目標**：完成技術研究和架構設計

**交付物**：
- `research.md`：技術決策和研究結果
- `data-model.md`：資料模型定義
- `contracts/`：API 合約（OpenAPI 規格）
- `quickstart.md`：快速開始指南

**任務**：
1. 研究 Cloudflare Turnstile 整合方式（demo 模式）
2. 研究 Redis 佇列實作最佳實踐
3. 研究 Redis Lua 腳本庫存控制模式
4. 設計資料模型（商品、佇列、會話）
5. 設計 API 端點和合約
6. 設計 WebSocket/SSE 推送機制

### 階段 1：基礎架構（MVP 最小版本）

**目標**：建立可運行的最小系統

**交付物**：
- Docker Compose 配置
- FastAPI 基礎架構
- Redis 配置
- 基本的 API 端點（商品查詢、加入佇列）

**任務**：
1. 建立 Docker Compose 配置（FastAPI + Redis）
2. 建立 FastAPI 專案結構
3. 建立 Vue 前端專案結構
4. 實作基本的商品查詢 API
5. 實作基本的佇列加入 API（加入 `queue:waiting`）
6. 實作系統後台任務：從 `queue:waiting` 移入 `queue:active`（定期執行）
7. 實作基本的佇列位置查詢 API（分別查詢 waiting 和 active 位置）
8. 建立基本的 Vue 介面（商品展示、加入佇列、顯示佇列狀態）

**驗收標準**：
- Docker Compose 可以成功啟動所有服務
- 可以透過 API 查詢商品資訊
- 可以加入 `queue:waiting` 並查詢位置
- 系統後台可以從 `queue:waiting` 移入 `queue:active`
- 可以分別查詢在 waiting 和 active 中的位置
- 前端可以顯示商品和佇列狀態（waiting 和 active）

### 階段 2：反爬蟲與購買流程

**目標**：完成反爬蟲整合和購買流程

**交付物**：
- Turnstile 整合（前端 + 後端驗證）
- 購買處理 API
- 庫存管理（Lua 腳本）
- 完整的購買流程介面

**任務**：
1. 整合 Cloudflare Turnstile（前端 widget）
2. 實作 Turnstile token 後端驗證
3. 實作 Redis Lua 腳本（庫存扣減）
4. 實作購買處理 API（**只允許 `queue:active` 中位置為 0 的使用者購買**）
5. 實作購買時限管理
6. 實作購買完成或超時後，從 `queue:active` 移除並從 `queue:waiting` 補充新人的邏輯
7. 完成 Vue 購買流程介面
8. 實作結果顯示頁面

**驗收標準**：
- Turnstile 驗證可以正常運作（demo 模式）
- 只有 `queue:active` 中位置為 0 的使用者可以購買
- 可以完成購買流程
- 庫存扣減準確，無超賣
- 購買時限管理正常
- 購買完成或超時後，系統自動從 `queue:waiting` 補充新人到 `queue:active`

### 階段 3：即時更新與優化

**目標**：完成即時更新和系統優化

**交付物**：
- WebSocket/SSE 佇列狀態推送
- 錯誤處理和日誌
- 效能優化
- 測試覆蓋

**任務**：
1. 實作 WebSocket 或 SSE 佇列狀態推送
2. 前端整合即時更新
3. 完善錯誤處理
4. 新增日誌記錄
5. 效能測試和優化
6. 撰寫單元測試和整合測試
7. 達到測試覆蓋率目標

**驗收標準**：
- 佇列狀態可以即時更新（延遲 ≤ 5 秒）
- 錯誤處理完善
- 測試覆蓋率達標（≥ 80%）
- 系統可以處理至少 1000 個並發使用者

## 資料模型

### 商品（Product）

- `id`: 商品 ID（字串）
- `name`: 商品名稱（字串）
- `image_url`: 商品圖片 URL（字串）
- `price`: 價格（數字）
- `total_stock`: 總庫存（整數，固定為 5）
- `remaining_stock`: 剩餘庫存（整數，Redis 中儲存）

### 兩階段佇列

**排隊區 (queue:waiting)**：
- `user_session_id`: 使用者會話 ID（字串，Redis key）
- `position_waiting`: 在排隊區的位置（整數）
- `joined_at`: 加入排隊區的時間（時間戳）
- `status`: 狀態（waiting - 在排隊區等待進入搖滾區）

**搖滾區 (queue:active)**：
- `user_session_id`: 使用者會話 ID（字串，Redis key）
- `position_active`: 在搖滾區的位置（整數，0 表示輪到購買）
- `entered_active_at`: 進入搖滾區的時間（時間戳）
- `status`: 狀態（active - 在搖滾區等待, ready_to_purchase - 輪到購買, purchased - 已購買, expired - 超時）

### 會話（Session）

- `session_id`: 會話 ID（字串，Redis key）
- `turnstile_verified`: Turnstile 驗證狀態（布林值）
- `verified_at`: 驗證時間（時間戳）
- `queue_position`: 當前佇列位置（整數，可選）

## API 設計概要

### REST API 端點

- `GET /api/products`: 取得商品列表
- `GET /api/products/{product_id}`: 取得商品詳情
- `POST /api/queue/join`: 加入佇列（**必須先通過 Turnstile 驗證**，驗證失敗無法加入，成功後加入 `queue:waiting`）
- `GET /api/queue/status`: 查詢佇列狀態（返回在 waiting 和 active 中的位置）
- `POST /api/purchase`: 處理購買（**只允許 `queue:active` 中位置為 0 的使用者**）
- `GET /api/queue/position`: 查詢佇列位置（分別返回 waiting 和 active 位置）

### WebSocket/SSE

- `WS /api/queue/stream`: 佇列狀態即時推送

詳細 API 規格見 `contracts/` 目錄。

## 文件要求

- [x] API 文件：OpenAPI 規格（自動生成）
- [ ] 使用者文件：使用說明（正體中文）
- [ ] 開發者文件：架構說明、部署指南（正體中文）
- [ ] 快速開始指南：`quickstart.md`

## 風險評估

### 技術風險

1. **Redis 單點故障**
   - **風險**：Redis 故障導致系統無法運作
   - **應對**：MVP 階段接受單點故障，未來可加入 Redis Sentinel 或 Cluster

2. **Turnstile 假金鑰限制**
   - **風險**：假金鑰可能無法完整模擬真實場景
   - **應對**：明確標註為 demo 模式，僅用於展示

3. **高併發效能**
   - **風險**：1000+ 並發使用者可能影響效能
   - **應對**：使用 Redis 高效能特性，進行負載測試和優化

### 業務風險

1. **庫存超賣**
   - **風險**：併發購買可能導致超賣
   - **應對**：使用 Redis Lua 腳本確保原子性，嚴格測試

2. **佇列順序錯誤**
   - **風險**：併發加入佇列可能導致順序錯誤
   - **應對**：使用 Redis Sorted Set 和原子操作，嚴格測試

## 驗收標準

- [ ] 功能符合 MVP 要求：所有核心功能實作完成
- [ ] 測試覆蓋率達標：核心邏輯 ≥ 80%
- [ ] 程式碼通過品質檢查：通過靜態分析工具
- [ ] 文件完整且使用正體中文：所有文件使用正體中文
- [ ] Docker Compose 可以一鍵啟動：`docker-compose up` 成功啟動所有服務
- [ ] 系統可以進行展示：完整流程可以順利執行
- [ ] 反爬蟲機制有效：可以阻擋至少 80% 的簡單自動化請求
- [ ] 庫存管理準確：無超賣情況
- [ ] 佇列順序正確：嚴格按時間順序
- [ ] 即時更新正常：佇列狀態更新延遲 ≤ 5 秒
