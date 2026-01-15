"""
API 整合測試
"""
import pytest
from app.services.product_service import ProductService
from app.services.session_service import SessionService


class TestProductsAPI:
    """商品 API 測試"""
    
    def test_get_products(self, client):
        """測試取得商品列表"""
        ProductService.initialize_products()
        
        response = client.get("/api/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert len(data["products"]) == 3
    
    def test_get_product(self, client):
        """測試取得商品詳情"""
        ProductService.initialize_products()
        
        response = client.get("/api/products/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "1"
        assert data["total_stock"] == 5
    
    def test_get_product_not_found(self, client):
        """測試取得不存在的商品"""
        response = client.get("/api/products/999")
        assert response.status_code == 404


class TestQueueAPI:
    """佇列 API 測試"""
    
    def test_join_queue_without_token(self, client):
        """測試沒有 token 加入佇列"""
        ProductService.initialize_products()
        
        response = client.post(
            "/api/queue/join",
            json={
                "product_id": "1",
                "turnstile_token": ""
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error"] == "INVALID_TURNSTILE_TOKEN"
    
    def test_get_queue_status_not_found(self, client):
        """測試查詢不存在的佇列狀態"""
        response = client.get(
            "/api/queue/status",
            params={
                "session_id": "nonexistent",
                "product_id": "1"
            }
        )
        assert response.status_code == 404


class TestPurchaseAPI:
    """購買 API 測試"""
    
    def test_purchase_not_in_queue(self, client):
        """測試不在佇列中的人嘗試購買"""
        ProductService.initialize_products()
        session_id = SessionService.create_session(turnstile_verified=True)
        
        response = client.post(
            "/api/purchase",
            json={
                "product_id": "1",
                "quantity": 1,
                "session_id": session_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["error"] == "NOT_READY"
