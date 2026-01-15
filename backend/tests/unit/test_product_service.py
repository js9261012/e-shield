"""
商品服務單元測試
"""
import pytest
from app.services.product_service import ProductService
from app.core.redis import get_redis_client


class TestProductService:
    """商品服務測試"""
    
    def test_initialize_products(self, redis_client):
        """測試初始化商品"""
        ProductService.initialize_products()
        
        # 檢查商品是否建立
        products = ProductService.get_all_products()
        assert len(products) == 3
        
        # 檢查庫存
        stock = redis_client.get("product:stock:1")
        assert stock == "5"
    
    def test_get_product(self, redis_client):
        """測試取得商品"""
        ProductService.initialize_products()
        
        product = ProductService.get_product("1")
        assert product is not None
        assert product.id == "1"
        assert product.total_stock == 5
        assert product.remaining_stock == 5
    
    def test_get_product_not_found(self):
        """測試取得不存在的商品"""
        product = ProductService.get_product("999")
        assert product is None
    
    def test_get_all_products(self, redis_client):
        """測試取得所有商品"""
        ProductService.initialize_products()
        
        products = ProductService.get_all_products()
        assert len(products) == 3
        assert all(p.total_stock == 5 for p in products)
