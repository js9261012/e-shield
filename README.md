# E-Shield 反爬蟲排隊系統

用於搶購稀有球鞋的反爬蟲排隊系統，使用 FastAPI、Vue 3、Redis 和 Cloudflare Turnstile 實作。

## 專案結構

```
e-shield/
├── backend/              # FastAPI 後端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心模組（Redis 連線等）
│   │   ├── models/      # 資料模型
│   │   ├── services/    # 業務邏輯服務
│   │   ├── tasks/       # 後台任務
│   │   └── scripts/     # Lua 腳本
│   ├── tests/           # 測試
│   ├── Dockerfile       # Docker 映像檔
│   └── requirements.txt # Python 依賴
├── frontend/            # Vue 3 前端
│   ├── src/
│   └── package.json
├── docker-compose.yml   # Docker Compose 配置
└── specs/               # 專案規格文件
```

## 技術棧

- **後端**: FastAPI (Python 3.11+)
- **前端**: Vue 3
- **資料庫**: Redis 7.x
- **反爬蟲**: Cloudflare Turnstile (測試模式)
- **容器化**: Docker Compose

## 快速開始

### 前置需求

- Docker 20.10+
- Docker Compose 2.0+

### 啟動服務

```bash
# 啟動所有服務（Redis、FastAPI、Frontend）
docker compose up -d

# 查看所有服務日誌
docker compose logs -f

# 查看特定服務日誌
docker compose logs -f frontend
docker compose logs -f fastapi

# 停止服務
docker compose down

# 重建並啟動服務
docker compose up -d --build
```

### 驗證服務

- **前端應用**: http://localhost:3000
- **API 文件**: http://localhost:8000/docs
- **健康檢查**: http://localhost:8000/api/health
- **商品列表 API**: http://localhost:8000/api/products

## 功能特性

### 已實作（Phase 1-5）

- ✅ Docker Compose 環境配置
- ✅ FastAPI 後端基礎架構
- ✅ Redis 連線和配置
- ✅ 商品管理（初始化、查詢）
- ✅ 兩階段佇列系統（queue:waiting 和 queue:active）
- ✅ 會話管理
- ✅ 庫存管理（Lua 腳本原子操作）
- ✅ 購買流程 API
- ✅ 佇列管理後台任務
- ✅ Cloudflare Turnstile 反爬蟲整合（測試模式）
- ✅ 速率限制中間件
- ✅ Vue 3 前端介面（商品列表、詳情、佇列狀態、購買）
- ✅ Turnstile Widget 元件
- ✅ SSE 即時佇列狀態更新

### 已實作（Phase 6）

- ✅ 全域錯誤處理中間件
- ✅ 結構化日誌記錄系統
- ✅ 單元測試（服務層邏輯）
- ✅ 整合測試（API 端點和 Redis 互動）
- ✅ 關鍵操作日誌記錄

## API 端點

### 商品

- `GET /api/products` - 取得商品列表
- `GET /api/products/{product_id}` - 取得商品詳情

### 佇列

- `POST /api/queue/join` - 加入佇列（加入 queue:waiting）
- `GET /api/queue/status` - 查詢佇列狀態

### 購買

- `POST /api/purchase` - 處理購買（只允許 queue:active 位置 0 的使用者）

### 健康檢查

- `GET /api/health` - 健康檢查

## 環境變數

複製 `.env.example` 為 `.env` 並設定：

```env
REDIS_URL=redis://localhost:6379
TURNSTILE_SITE_KEY=1x00000000000000000000AA
TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AA
DEBUG=true
LOG_LEVEL=INFO
```

## 開發

### 後端開發

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端開發

```bash
cd frontend
npm install
npm run dev
```

## 測試

### 執行測試

```bash
# 進入後端目錄
cd backend

# 安裝測試依賴
pip install -r requirements.txt

# 執行所有測試
pytest

# 執行單元測試
pytest tests/unit/

# 執行整合測試
pytest tests/integration/

# 查看測試覆蓋率
pytest --cov=app --cov-report=html
```

### 測試結構

- `tests/unit/`: 單元測試（服務層邏輯）
- `tests/integration/`: 整合測試（API 端點和 Redis 互動）

## 專案狀態

目前已完成 Phase 1-6 的所有核心功能實作：
- ✅ 專案設定與基礎架構
- ✅ 基礎功能與資料模型
- ✅ User Story 1: 正常使用者購買流程（完整前後端）
- ✅ User Story 2: Turnstile 反爬蟲整合
- ✅ User Story 3: SSE 即時佇列狀態更新
- ✅ 優化與完善（錯誤處理、日誌、測試）

**系統已完整實作，可進行完整展示和測試！** 🎉

## 授權

MIT License
