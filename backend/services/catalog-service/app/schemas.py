from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class ProductItem(BaseModel):
    product_id: str = Field(..., min_length=1)
    sku: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    cost_price: float = Field(..., ge=0)
    retail_price: float = Field(..., ge=0)
    stock_quantity: int = Field(..., ge=0)
    reorder_level: int = Field(..., ge=0)
    unit: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    is_active: bool


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    cost_price: float = Field(..., ge=0)
    retail_price: float = Field(..., ge=0)
    stock_quantity: int = Field(..., ge=0)
    reorder_level: int = Field(..., ge=0)
    unit: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    is_active: bool = True


class ProductUpdate(ProductCreate):
    pass


class ProductDeleteResponse(BaseModel):
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class Supplier(BaseModel):
    supplier_id: str = Field(..., min_length=1)
    supplier_code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    contact_name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    rating: float = Field(..., ge=0, le=5)
    lead_time_days: int = Field(..., ge=0)
    status: str = Field(..., min_length=1)


class SupplierCreate(BaseModel):
    supplier_code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    contact_name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    rating: float = Field(..., ge=0, le=5)
    lead_time_days: int = Field(..., ge=0)
    status: str = Field(..., min_length=1)


class SupplierUpdate(SupplierCreate):
    pass


class SupplierDeleteResponse(BaseModel):
    supplier_id: str = Field(..., min_length=1)
    supplier_name: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class SupplierOffer(BaseModel):
    offer_id: str = Field(..., min_length=1)
    offer_code: str = Field(..., min_length=1)
    offer_title: str = Field(..., min_length=1)
    supplier_id: str = Field(..., min_length=1)
    supplier_name: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1)
    min_order_quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)
    discount_percent: float = Field(..., ge=0, le=100)
    start_date: str = Field(..., min_length=1)
    end_date: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    notes: str = Field(..., min_length=1)
