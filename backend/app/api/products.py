"""
商品 API
"""
from fastapi import APIRouter, HTTPException
from app.services.product_service import ProductService
from app.models.product import Product, ProductListResponse

router = APIRouter()


@router.get("/products", response_model=ProductListResponse)
async def get_products():
    """取得商品列表"""
    products = ProductService.get_all_products()
    return ProductListResponse(products=products)


@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """取得商品詳情"""
    product = ProductService.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product
