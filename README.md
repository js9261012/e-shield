# E-Shield 反爬蟲排隊系統

## 專案簡介

E-Shield 是一個專為搶購稀有商品（如限量球鞋）設計的反爬蟲排隊系統。系統採用兩階段佇列機制，結合 Cloudflare Turnstile 驗證，有效防止機器人和爬蟲程式，確保公平的購買流程。

### 核心特色

- 🛡️ **反爬蟲保護**: 整合 Cloudflare Turnstile，有效阻擋機器人
- 🎯 **兩階段佇列**: 排隊區（waiting）→ 搖滾區（active）→ 購買，確保公平性
- ⚡ **高效能**: 使用 Redis 和 Lua 腳本確保庫存操作的原子性，防止超賣
- 📊 **即時更新**: SSE（Server-Sent Events）即時推送佇列狀態
- 🚀 **容器化部署**: Docker Compose 一鍵啟動所有服務

### 技術棧

- **後端**: FastAPI (Python 3.11+)
- **前端**: Vue 3
- **資料庫**: Redis 7.x
- **反爬蟲**: Cloudflare Turnstile (測試模式)
- **容器化**: Docker Compose

### 啟動步驟

```bash
docker compose up -d
```

啟動後可訪問：
- 前端應用: http://localhost:3000
- API 文件: http://localhost:8000/docs

