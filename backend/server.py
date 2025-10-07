from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import jwt
import bcrypt
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="OrderBuddy API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-here')

# Tamil Nadu Districts and Taluks Data
TAMIL_NADU_LOCATIONS = {
    "Chennai": {
        "taluks": {
            "Chennai North": ["Washermanpet", "Royapuram", "Tondiarpet", "Madhavaram"],
            "Chennai Central": ["Egmore", "Purasawalkam", "Kilpauk", "Anna Nagar"],
            "Chennai South": ["Guindy", "Adyar", "Velachery", "Sholinganallur"]
        }
    },
    "Coimbatore": {
        "taluks": {
            "Coimbatore North": ["RS Puram", "Gandhipuram", "Peelamedu", "Saravanampatti"],
            "Coimbatore South": ["Singanallur", "Podanur", "Sulur", "Madukkarai"],
            "Pollachi": ["Pollachi", "Valparai", "Udumalaipettai", "Kinathukadavu"]
        }
    },
    "Madurai": {
        "taluks": {
            "Madurai East": ["Thiruparankundram", "Koodal Nagar", "Anna Nagar", "Goripalayam"],
            "Madurai West": ["West Masi Street", "Periyar", "Vilangudi", "Tiruppalai"],
            "Melur": ["Melur", "Vadipatti", "Thirumangalam", "Usilampatti"]
        }
    }
}

# Pydantic Models
class UserBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    phone: str
    user_type: str  # 'customer', 'shop_owner', 'delivery_person'
    district: str
    taluk: str
    village_city: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    phone: str
    user_type: str
    district: str
    taluk: str
    village_city: str

class UserLogin(BaseModel):
    email: str
    password: str

class Shop(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    owner_id: str
    district: str
    taluk: str
    village_city: str
    is_open: bool = True
    opening_time: str = "09:00"
    closing_time: str = "21:00"
    rating: float = 0.0
    total_ratings: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ShopCreate(BaseModel):
    name: str
    description: str
    district: str
    taluk: str
    village_city: str
    opening_time: str = "09:00"
    closing_time: str = "21:00"

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    shop_id: str
    category: str
    stock_quantity: int
    image_url: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    stock_quantity: int
    image_url: str = ""

class CartItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    product_id: str
    quantity: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CartItemCreate(BaseModel):
    product_id: str
    quantity: int

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    shop_id: str
    delivery_person_id: Optional[str] = None
    items: List[Dict[str, Any]]  # product_id, quantity, price, name
    total_amount: float
    status: str = "pending"  # pending, packed, on_the_way, delivered, cancelled
    delivery_address: str
    otp: str = Field(default="1234")  # Simple OTP for demo
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: Optional[datetime] = None

class OrderCreate(BaseModel):
    shop_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    delivery_address: str

class AIAssistantRequest(BaseModel):
    message: str
    user_id: str
    context: str = "general"  # product_search, order_help, general

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_data: dict) -> str:
    return jwt.encode(user_data, SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_data = verify_jwt_token(token)
    user = await db.users.find_one({"id": user_data["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return UserBase(**user)

def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, list):
                data[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
    return data

def parse_from_mongo(item):
    """Parse datetime strings back from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if key in ['created_at', 'delivered_at'] and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value)
                except:
                    pass
    return item

# Authentication Routes
@api_router.post("/auth/register")
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate location data
    if user_data.district not in TAMIL_NADU_LOCATIONS:
        raise HTTPException(status_code=400, detail="Invalid district")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_dict = user_data.dict()
    del user_dict['password']
    user = UserBase(**user_dict)
    user_dict = prepare_for_mongo(user.dict())
    user_dict['password'] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Create JWT token
    token = create_jwt_token({"user_id": user.id, "email": user.email, "user_type": user.user_type})
    
    return {
        "message": "User registered successfully",
        "user": user,
        "token": token
    }

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    # Find user
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token = create_jwt_token({"user_id": user["id"], "email": user["email"], "user_type": user["user_type"]})
    
    user_obj = UserBase(**parse_from_mongo(user))
    
    return {
        "message": "Login successful",
        "user": user_obj,
        "token": token
    }

# Location Routes
@api_router.get("/locations")
async def get_locations():
    return TAMIL_NADU_LOCATIONS

# Shop Routes
@api_router.post("/shops", dependencies=[Depends(get_current_user)])
async def create_shop(shop_data: ShopCreate, current_user: UserBase = Depends(get_current_user)):
    if current_user.user_type != "shop_owner":
        raise HTTPException(status_code=403, detail="Only shop owners can create shops")
    
    shop = Shop(**shop_data.dict(), owner_id=current_user.id)
    shop_dict = prepare_for_mongo(shop.dict())
    await db.shops.insert_one(shop_dict)
    
    return {"message": "Shop created successfully", "shop": shop}

@api_router.get("/shops")
async def get_shops(district: str = None, taluk: str = None, village_city: str = None):
    filter_query = {}
    if district:
        filter_query["district"] = district
    if taluk:
        filter_query["taluk"] = taluk
    if village_city:
        filter_query["village_city"] = village_city
    
    shops = await db.shops.find(filter_query, {"_id": 0}).to_list(1000)
    return [Shop(**parse_from_mongo(shop)) for shop in shops]

@api_router.get("/shops/my")
async def get_my_shops(current_user: UserBase = Depends(get_current_user)):
    if current_user.user_type != "shop_owner":
        raise HTTPException(status_code=403, detail="Only shop owners can access this")
    
    shops = await db.shops.find({"owner_id": current_user.id}, {"_id": 0}).to_list(1000)
    return [Shop(**parse_from_mongo(shop)) for shop in shops]

# Product Routes
@api_router.post("/shops/{shop_id}/products")
async def create_product(shop_id: str, product_data: ProductCreate, current_user: UserBase = Depends(get_current_user)):
    # Verify shop ownership
    shop = await db.shops.find_one({"id": shop_id, "owner_id": current_user.id})
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found or not owned by user")
    
    product = Product(**product_data.dict(), shop_id=shop_id)
    product_dict = prepare_for_mongo(product.dict())
    await db.products.insert_one(product_dict)
    
    return {"message": "Product created successfully", "product": product}

@api_router.get("/shops/{shop_id}/products")
async def get_shop_products(shop_id: str):
    products = await db.products.find({"shop_id": shop_id, "is_active": True}, {"_id": 0}).to_list(1000)
    return [Product(**parse_from_mongo(product)) for product in products]

@api_router.get("/products/search")
async def search_products(query: str = "", district: str = None, taluk: str = None, category: str = None):
    # Build filter for location-based shops
    shop_filter = {}
    if district:
        shop_filter["district"] = district
    if taluk:
        shop_filter["taluk"] = taluk
    
    # Get shops in the area
    shops = await db.shops.find(shop_filter).to_list(1000)
    shop_ids = [shop["id"] for shop in shops]
    
    # Build product filter
    product_filter = {"shop_id": {"$in": shop_ids}, "is_active": True}
    if category:
        product_filter["category"] = category
    if query:
        product_filter["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}}
        ]
    
    products = await db.products.find(product_filter).to_list(1000)
    return [Product(**parse_from_mongo(product)) for product in products]

# Cart Routes
@api_router.post("/cart")
async def add_to_cart(cart_item: CartItemCreate, current_user: UserBase = Depends(get_current_user)):
    if current_user.user_type != "customer":
        raise HTTPException(status_code=403, detail="Only customers can add to cart")
    
    # Check if item already exists in cart
    existing_item = await db.cart.find_one({
        "customer_id": current_user.id,
        "product_id": cart_item.product_id
    })
    
    if existing_item:
        # Update quantity
        new_quantity = existing_item["quantity"] + cart_item.quantity
        await db.cart.update_one(
            {"id": existing_item["id"]},
            {"$set": {"quantity": new_quantity}}
        )
        return {"message": "Cart updated successfully"}
    else:
        # Add new item
        item = CartItem(**cart_item.dict(), customer_id=current_user.id)
        item_dict = prepare_for_mongo(item.dict())
        await db.cart.insert_one(item_dict)
        return {"message": "Item added to cart successfully"}

@api_router.get("/cart")
async def get_cart(current_user: UserBase = Depends(get_current_user)):
    if current_user.user_type != "customer":
        raise HTTPException(status_code=403, detail="Only customers can access cart")
    
    cart_items = await db.cart.find({"customer_id": current_user.id}, {"_id": 0}).to_list(1000)
    
    # Get product details for each cart item
    enriched_items = []
    for item in cart_items:
        # Parse cart item from mongo to handle datetime fields
        parsed_item = parse_from_mongo(item)
        
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0})
        if product:
            enriched_item = {
                **parsed_item,
                "product": Product(**parse_from_mongo(product))
            }
            enriched_items.append(enriched_item)
    
    return enriched_items

@api_router.delete("/cart/{item_id}")
async def remove_from_cart(item_id: str, current_user: UserBase = Depends(get_current_user)):
    result = await db.cart.delete_one({"id": item_id, "customer_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Item removed from cart"}

# Order Routes
@api_router.post("/orders")
async def create_order(order_data: OrderCreate, current_user: UserBase = Depends(get_current_user)):
    if current_user.user_type != "customer":
        raise HTTPException(status_code=403, detail="Only customers can place orders")
    
    order = Order(**order_data.dict(), customer_id=current_user.id)
    order_dict = prepare_for_mongo(order.dict())
    await db.orders.insert_one(order_dict)
    
    # Clear cart items for this order
    product_ids = [item["product_id"] for item in order_data.items]
    await db.cart.delete_many({
        "customer_id": current_user.id,
        "product_id": {"$in": product_ids}
    })
    
    return {"message": "Order placed successfully", "order": order}

@api_router.get("/orders")
async def get_orders(current_user: UserBase = Depends(get_current_user)):
    if current_user.user_type == "customer":
        orders = await db.orders.find({"customer_id": current_user.id}).to_list(1000)
    elif current_user.user_type == "shop_owner":
        # Get orders for shops owned by this user
        shops = await db.shops.find({"owner_id": current_user.id}).to_list(1000)
        shop_ids = [shop["id"] for shop in shops]
        orders = await db.orders.find({"shop_id": {"$in": shop_ids}}).to_list(1000)
    elif current_user.user_type == "delivery_person":
        orders = await db.orders.find({"delivery_person_id": current_user.id}).to_list(1000)
    else:
        orders = []
    
    return [Order(**parse_from_mongo(order)) for order in orders]

class OrderStatusUpdate(BaseModel):
    status: str

@api_router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, status_update: OrderStatusUpdate, current_user: UserBase = Depends(get_current_user)):
    # Verify user can update this order
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check permissions
    can_update = False
    if current_user.user_type == "shop_owner":
        shop = await db.shops.find_one({"id": order["shop_id"], "owner_id": current_user.id})
        if shop:
            can_update = True
    elif current_user.user_type == "delivery_person" and order.get("delivery_person_id") == current_user.id:
        can_update = True
    
    if not can_update:
        raise HTTPException(status_code=403, detail="Not authorized to update this order")
    
    update_data = {"status": status_update.status}
    if status_update.status == "delivered":
        update_data["delivered_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.orders.update_one({"id": order_id}, {"$set": update_data})
    
    return {"message": "Order status updated successfully"}

# AI Assistant Route
@api_router.post("/ai/assistant")
async def ai_assistant(request: AIAssistantRequest, current_user: UserBase = Depends(get_current_user)):
    try:
        # Initialize AI chat with Emergent LLM key
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"orderbuddy_{current_user.id}",
            system_message=f"""You are OrderBuddy AI Assistant, helping users with their shopping needs in Tamil Nadu. 
            You are assisting a {current_user.user_type} named {current_user.name} from {current_user.village_city}, {current_user.taluk}, {current_user.district}.
            
            Context: {request.context}
            
            Be helpful, friendly, and provide concise responses about:
            - Product recommendations
            - Order assistance
            - Shop information
            - Local shopping guidance
            
            Always respond in a helpful and professional manner."""
        ).with_model("openai", "gpt-4o-mini")
        
        # Create user message
        user_message = UserMessage(text=request.message)
        
        # Get AI response
        response = await chat.send_message(user_message)
        
        return {
            "response": response,
            "context": request.context,
            "user_location": f"{current_user.village_city}, {current_user.taluk}, {current_user.district}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Assistant error: {str(e)}")

# Dashboard Routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: UserBase = Depends(get_current_user)):
    if current_user.user_type == "shop_owner":
        # Get shop owner statistics
        shops = await db.shops.find({"owner_id": current_user.id}).to_list(1000)
        shop_ids = [shop["id"] for shop in shops]
        
        total_shops = len(shops)
        total_products = await db.products.count_documents({"shop_id": {"$in": shop_ids}})
        total_orders = await db.orders.count_documents({"shop_id": {"$in": shop_ids}})
        
        return {
            "total_shops": total_shops,
            "total_products": total_products,
            "total_orders": total_orders,
            "user_type": "shop_owner"
        }
    
    elif current_user.user_type == "customer":
        total_orders = await db.orders.count_documents({"customer_id": current_user.id})
        cart_items = await db.cart.count_documents({"customer_id": current_user.id})
        
        return {
            "total_orders": total_orders,
            "cart_items": cart_items,
            "user_type": "customer"
        }
    
    elif current_user.user_type == "delivery_person":
        total_deliveries = await db.orders.count_documents({"delivery_person_id": current_user.id})
        pending_deliveries = await db.orders.count_documents({
            "delivery_person_id": current_user.id,
            "status": {"$in": ["on_the_way", "packed"]}
        })
        
        return {
            "total_deliveries": total_deliveries,
            "pending_deliveries": pending_deliveries,
            "user_type": "delivery_person"
        }

# Health check route
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "OrderBuddy API is running"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()