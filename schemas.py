from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# Users
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    address: Optional[str] = Field(None, description="Address")
    is_active: bool = Field(True, description="Whether user is active")

# Products
class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
    image: Optional[str] = Field(None, description="Main image URL")
    rating: Optional[float] = Field(0.0, ge=0, le=5, description="Average rating")

# Orders
class OrderItem(BaseModel):
    product_id: str
    title: str
    quantity: int = Field(..., ge=1)
    price: float = Field(..., ge=0)

class Order(BaseModel):
    customer_name: str
    customer_email: EmailStr
    shipping_address: str
    items: List[OrderItem]
    total_amount: Optional[float] = 0
    status: str = "pending"
