# 快速開始指南

**功能**：反爬蟲排隊系統  
**日期**：2025-01-27

## 概述

本指南幫助您快速啟動和運行反爬蟲排隊系統。

## 前置需求

- Docker 20.10+
- Docker Compose 2.0+
- Git（用於克隆專案）

## 快速啟動

### 1. 克隆專案（如果尚未完成）

```bash
git clone <repository-url>
cd e-shield
```

### 2. 啟動服務

```bash
docker-compose up -d
```

這將啟動以下服務：
- **FastAPI 後端**：http://localhost:8000
- **Redis**：localhost:6379
- **Vue 前端**：http://localhost:3000（如果包含前端容器）

### 3. 驗證服務

#### 檢查 FastAPI 後端

```bash
curl http://localhost:8000/api/products
```

預期回應：
```json
{
  "products": [
    {
      "id": "1",
      "name": "限量球鞋 A",
      "image_url": "https://example.com/shoe-a.jpg",
      "price": 9999,
      "total_stock": 5,
      "remaining_stock": 5
    }
  ]
}
```

#### 檢查 Redis

```bash
docker-compose exec redis redis-cli ping
```

預期回應：`PONG`

#### 檢查 API 文件

開啟瀏覽器訪問：http://localhost:8000/docs

您應該看到 FastAPI 自動生成的 Swagger UI。

### 4. 初始化資料

系統啟動時會自動初始化商品資料（5 雙球鞋）。如果需要手動初始化：

```bash
# 進入 FastAPI 容器
docker-compose exec fastapi bash

# 執行初始化腳本（如果有的話）
python scripts/init_data.py
```

## 使用流程

### 1. 查看商品

訪問前端頁面或使用 API：

```bash
curl http://localhost:8000/api/products
```

### 2. 加入佇列

1. 在前端頁面點擊「加入排隊」
2. 完成 Turnstile 驗證（使用測試模式，自動通過）
3. 系統會返回會話 ID 和佇列位置

或使用 API：

```bash
curl -X POST http://localhost:8000/api/queue/join \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "1",
    "turnstile_token": "test_token"
  }'
```

### 3. 查詢佇列狀態

使用會話 ID 查詢：

```bash
curl "http://localhost:8000/api/queue/status?session_id=YOUR_SESSION_ID&product_id=1"
```

### 4. 監聽即時更新（SSE）

```bash
curl "http://localhost:8000/api/queue/stream?session_id=YOUR_SESSION_ID&product_id=1"
```

### 5. 購買

當輪到您時（queue_position = 0），可以購買：

```bash
curl -X POST http://localhost:8000/api/purchase \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "1",
    "quantity": 1,
    "session_id": "YOUR_SESSION_ID"
  }'
```

## 環境變數

### FastAPI 容器

在 `docker-compose.yml` 或 `.env` 檔案中設定：

```env
# Redis 連線
REDIS_URL=redis://redis:6379

# Turnstile 設定（測試模式）
TURNSTILE_SITE_KEY=1x00000000000000000000AA
TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AA

# 應用設定
DEBUG=true
LOG_LEVEL=INFO
```

### Redis 容器

預設配置即可，無需額外環境變數。

## 測試

### 執行單元測試

```bash
docker-compose exec fastapi pytest
```

### 執行整合測試

```bash
docker-compose exec fastapi pytest tests/integration/
```

### 執行端對端測試

```bash
# 需要先啟動服務
docker-compose up -d

# 執行 E2E 測試
npm run test:e2e  # 如果前端有測試腳本
```

## 常見問題

### 1. 服務無法啟動

**問題**：`docker-compose up` 失敗

**解決方案**：
- 檢查 Docker 是否運行：`docker ps`
- 檢查端口是否被占用：`lsof -i :8000` 或 `lsof -i :6379`
- 查看日誌：`docker-compose logs`

### 2. Redis 連線失敗

**問題**：FastAPI 無法連接到 Redis

**解決方案**：
- 確認 Redis 容器正在運行：`docker-compose ps`
- 檢查 Redis URL 環境變數
- 測試 Redis 連線：`docker-compose exec redis redis-cli ping`

### 3. Turnstile 驗證失敗

**問題**：無法通過 Turnstile 驗證

**解決方案**：
- 確認使用測試模式金鑰
- 檢查前端是否正確載入 Turnstile widget
- 查看瀏覽器控制台錯誤訊息

### 4. 佇列狀態不更新

**問題**：SSE 串流沒有更新

**解決方案**：
- 檢查 SSE 連線是否建立
- 查看後端日誌確認是否有推送
- 確認會話 ID 正確

## 開發模式

### 本地開發（不使用 Docker）

#### 後端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 啟動 Redis（需要單獨安裝）
redis-server

# 啟動 FastAPI
uvicorn main:app --reload
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

### 熱重載

Docker Compose 配置已包含熱重載支援，修改程式碼後會自動重啟服務。

## 日誌查看

### 查看所有服務日誌

```bash
docker-compose logs -f
```

### 查看特定服務日誌

```bash
docker-compose logs -f fastapi
docker-compose logs -f redis
```

## 停止服務

```bash
docker-compose down
```

清除所有資料（包括 Redis 資料）：

```bash
docker-compose down -v
```

## 重置系統

如果需要重置所有資料：

```bash
# 停止服務
docker-compose down -v

# 重新啟動
docker-compose up -d

# 重新初始化資料
docker-compose exec fastapi python scripts/init_data.py
```

## 下一步

- 閱讀 [資料模型文件](./data-model.md) 了解資料結構
- 閱讀 [API 文件](./contracts/openapi.yaml) 了解 API 端點
- 閱讀 [實作規劃](./plan.md) 了解開發計劃

## 支援

如有問題，請查看：
- 專案 README
- API 文件：http://localhost:8000/docs
- 開發者文件
