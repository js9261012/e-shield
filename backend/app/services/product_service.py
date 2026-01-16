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
        """初始化商品資料到 Redis"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("開始初始化商品資料")
        
        redis_client = get_redis_client()
        
        products = [
            {
                "id": "1",
                "name": "限量球鞋",
                "image_url": "/images/shoes.png",
                "price": 9999,
                "total_stock": 5
            }
        ]
        
        for product_data in products:
            product_id = product_data["id"]
            stock_key = ProductService._get_stock_key(product_id)
            product_key = ProductService._get_product_key(product_id)
            
            redis_client.set(stock_key, product_data["total_stock"])
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
        
        if not redis_client.exists(product_key):
            return None
        
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
    
    @staticmethod
    def reset_stock():
        """重置所有商品庫存為初始值"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("開始重置商品庫存")
        
        redis_client = get_redis_client()
        
        products = [
            {
                "id": "1",
                "name": "限量球鞋",
                "image_url": "/images/shoes.png",
                "price": 9999,
                "total_stock": 5
            }
        ]
        
        for product_data in products:
            product_id = product_data["id"]
            stock_key = ProductService._get_stock_key(product_id)
            product_key = ProductService._get_product_key(product_id)
            
            # 重置庫存為初始值
            redis_client.set(stock_key, product_data["total_stock"])
            
            # 確保商品資訊存在
            if not redis_client.exists(product_key):
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
        
        logger.info("商品庫存重置完成")
        return True
