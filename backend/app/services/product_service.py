"""
商品服務
"""
from typing import List, Optional
from app.core.redis import get_redis_client
from app.models.product import Product


class ProductService:
    """商品服務類別"""
    
    @staticmethod
    def _get_stock_key(product_id: str) -> str:
        """取得庫存 Redis key"""
        return f"product:stock:{product_id}"
    
    @staticmethod
    def _get_product_key(product_id: str) -> str:
        """取得商品資訊 Redis key"""
        return f"product:info:{product_id}"
    
    @staticmethod
    def initialize_products():
        """初始化商品資料到 Redis（加入日誌）"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("開始初始化商品資料")
        """
        初始化商品資料到 Redis
        建立 3 個測試商品，每個庫存 5 雙
        """
        redis_client = get_redis_client()
        
        products = [
            {
                "id": "1",
                "name": "限量球鞋",
                "image_url": "/images/shoes.png",  # 放在 frontend/public/images/ 資料夾
                "price": 9999,
                "total_stock": 5
            }
        ]
        
        for product_data in products:
            product_id = product_data["id"]
            stock_key = ProductService._get_stock_key(product_id)
            product_key = ProductService._get_product_key(product_id)
            
            # 設定庫存
            redis_client.set(stock_key, product_data["total_stock"])
            
            # 儲存商品資訊（使用 Hash）
            redis_client.hset(
                product_key,
                mapping={
                    "id": product_data["id"],
                    "name": product_data["name"],
                    "image_url": product_data["image_url"],
                    "price": str(product_data["price"]),
                    "total_stock": str(product_data["total_stock"])
                }
            )
    
    @staticmethod
    def get_all_products() -> List[Product]:
        """取得所有商品列表"""
        redis_client = get_redis_client()
        products = []
        
        # 取得所有商品 ID（從庫存 key 推斷）
        keys = redis_client.keys("product:stock:*")
        
        for key in keys:
            product_id = key.split(":")[-1]
            product = ProductService.get_product(product_id)
            if product:
                products.append(product)
        
        return products
    
    @staticmethod
    def get_product(product_id: str) -> Optional[Product]:
        """根據商品 ID 取得商品詳情"""
        redis_client = get_redis_client()
        
        product_key = ProductService._get_product_key(product_id)
        stock_key = ProductService._get_stock_key(product_id)
        
        # 檢查商品是否存在
        if not redis_client.exists(product_key):
            return None
        
        # 取得商品資訊
        product_info = redis_client.hgetall(product_key)
        remaining_stock = int(redis_client.get(stock_key) or 0)
        
        return Product(
            id=product_info.get("id", product_id),
            name=product_info.get("name", ""),
            image_url=product_info.get("image_url", ""),
            price=int(product_info.get("price", 0)),
            total_stock=int(product_info.get("total_stock", 0)),
            remaining_stock=remaining_stock
        )
