import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime

from database import db, create_document, get_documents
from bson import ObjectId

app = FastAPI(title="E-Commerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


# ---------- Product Models ----------
class CreateProduct(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: str
    in_stock: bool = True
    image: Optional[str] = None
    rating: Optional[float] = 0.0


class ProductOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    price: float
    category: str
    in_stock: bool
    image: Optional[str]
    rating: Optional[float]


# ---------- Order Models ----------
class OrderItem(BaseModel):
    product_id: str
    title: str
    quantity: int = Field(..., ge=1)
    price: float = Field(..., ge=0)

class CreateOrder(BaseModel):
    customer_name: str
    customer_email: str
    shipping_address: str
    items: List[OrderItem]

class OrderOut(BaseModel):
    id: str
    order_number: str
    total_amount: float
    items: List[OrderItem]
    status: str
    created_at: datetime


@app.get("/")
def root():
    return {"message": "E-Commerce API is running"}


@app.get("/products", response_model=List[ProductOut])
def list_products(q: Optional[str] = None, category: Optional[str] = None, limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_query = {}
    if q:
        filter_query["title"] = {"$regex": q, "$options": "i"}
    if category:
        filter_query["category"] = category

    docs = db.product.find(filter_query).limit(limit)
    products = []
    for d in docs:
        products.append(ProductOut(
            id=str(d.get("_id")),
            title=d.get("title"),
            description=d.get("description"),
            price=float(d.get("price", 0)),
            category=d.get("category", "General"),
            in_stock=bool(d.get("in_stock", True)),
            image=d.get("image"),
            rating=float(d.get("rating", 0.0)) if d.get("rating") is not None else 0.0,
        ))
    return products


@app.post("/products", status_code=201)
def create_product(payload: CreateProduct):
    product_dict = payload.model_dump()
    inserted_id = create_document("product", product_dict)
    return {"id": inserted_id}


@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product id")
    doc = db.product.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductOut(
        id=str(doc.get("_id")),
        title=doc.get("title"),
        description=doc.get("description"),
        price=float(doc.get("price", 0)),
        category=doc.get("category", "General"),
        in_stock=bool(doc.get("in_stock", True)),
        image=doc.get("image"),
        rating=float(doc.get("rating", 0.0)) if doc.get("rating") is not None else 0.0,
    )


@app.post("/orders", response_model=OrderOut, status_code=201)
def create_order(payload: CreateOrder):
    if len(payload.items) == 0:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    total = sum([it.price * it.quantity for it in payload.items])
    order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    order_doc = {
        "customer_name": payload.customer_name,
        "customer_email": payload.customer_email,
        "shipping_address": payload.shipping_address,
        "items": [it.model_dump() for it in payload.items],
        "total_amount": total,
        "order_number": order_number,
        "status": "pending",
    }

    inserted_id = create_document("order", order_doc)

    return OrderOut(
        id=inserted_id,
        order_number=order_number,
        total_amount=total,
        items=payload.items,
        status="pending",
        created_at=datetime.utcnow(),
    )


@app.get("/orders")
def list_orders(limit: int = 20):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    cursor = db.order.find({}).sort("created_at", -1).limit(limit)
    results = []
    for d in cursor:
        results.append({
            "id": str(d.get("_id")),
            "order_number": d.get("order_number"),
            "total_amount": d.get("total_amount"),
            "status": d.get("status"),
            "created_at": d.get("created_at"),
        })
    return {"orders": results}


@app.post("/seed")
def seed_products():
    """Seed the database with some sample products for demo purposes."""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    sample = [
        {
            "title": "Wireless Headphones",
            "description": "Noise-cancelling over-ear headphones with 30h battery.",
            "price": 99.99,
            "category": "Electronics",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1518443881150-2f81e7a0f34b?w=800&q=80",
            "rating": 4.5,
        },
        {
            "title": "Smart Watch",
            "description": "Fitness tracking, heart rate monitor, and notifications.",
            "price": 149.99,
            "category": "Wearables",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1511732351157-1865efcb7b7b?w=800&q=80",
            "rating": 4.2,
        },
        {
            "title": "Running Shoes",
            "description": "Lightweight and comfortable shoes for daily runs.",
            "price": 79.99,
            "category": "Footwear",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=800&q=80",
            "rating": 4.6,
        },
        {
            "title": "Backpack",
            "description": "Durable backpack with laptop compartment.",
            "price": 59.99,
            "category": "Accessories",
            "in_stock": True,
            "image": "https://images.unsplash.com/photo-1514477917009-389c76a86b68?w=800&q=80",
            "rating": 4.1,
        },
    ]

    inserted = 0
    for p in sample:
        existing = db.product.find_one({"title": p["title"]})
        if not existing:
            create_document("product", p)
            inserted += 1

    return {"inserted": inserted}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
