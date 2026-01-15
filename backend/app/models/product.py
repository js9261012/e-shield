"""
商品模型
"""
from pydantic import BaseModel, Field
from typing import Optional


class Product(BaseModel):
    """商品資料模型"""
    id: str = Field(..., description="商品 ID")
    name: str = Field(..., description="商品名稱")
    image_url: str = Field(..., description="商品圖片 URL")
    price: int = Field(..., description="價格（分）")
    total_stock: int = Field(..., description="總庫存")
    remaining_stock: int = Field(..., description="剩餘庫存")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1",
                "name": "限量球鞋 A",
                "image_url": "https://example.com/shoe-a.jpg",
                "price": 9999,
                "total_stock": 5,
                "remaining_stock": 5
            }
        }


class ProductListResponse(BaseModel):
    """商品列表回應"""
    products: list[Product]
