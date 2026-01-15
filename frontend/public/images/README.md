# 圖片資料夾

請將稀有球鞋的圖片放在這個資料夾中。

## 使用方式

1. 將圖片檔案（例如：`sneaker.jpg`）放在 `frontend/public/images/` 資料夾
2. 在 `backend/app/services/product_service.py` 中更新 `image_url` 為 `/images/sneaker.jpg`
3. 重新啟動服務即可

## 注意事項

- 圖片路徑以 `/` 開頭，會從 `public/` 資料夾根目錄開始
- 支援的圖片格式：jpg, jpeg, png, gif, webp
- 建議圖片尺寸：400x400 或更大
