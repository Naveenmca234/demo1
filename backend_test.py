#!/usr/bin/env python3
"""
OrderBuddy Backend API Testing Suite
Tests all backend functionality including authentication, shop management, cart operations, orders, AI assistant, and dashboard stats.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://shop-connect-tn.preview.emergentagent.com/api"
TIMEOUT = 30

class OrderBuddyTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        
        # Test data storage
        self.test_users = {}
        self.test_shops = {}
        self.test_products = {}
        self.test_orders = {}
        
        # Test results
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "errors": []
        }
    
    def log_result(self, test_name: str, success: bool, message: str = "", error: str = ""):
        """Log test result"""
        self.results["total_tests"] += 1
        if success:
            self.results["passed_tests"] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.results["failed_tests"] += 1
            error_msg = f"❌ {test_name}: {message} | Error: {error}"
            print(error_msg)
            self.results["errors"].append(error_msg)
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, token: str = None) -> tuple:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Set headers
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        if token:
            req_headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=req_headers, params=data)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=req_headers, json=data)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, headers=req_headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=req_headers)
            else:
                return None, f"Unsupported method: {method}"
            
            return response, None
        except requests.exceptions.RequestException as e:
            return None, str(e)
    
    def test_health_check(self):
        """Test API health check"""
        print("\n🔍 Testing Health Check...")
        
        response, error = self.make_request("GET", "/health")
        if error:
            self.log_result("Health Check", False, "Request failed", error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                self.log_result("Health Check", True, "API is healthy")
                return True
            else:
                self.log_result("Health Check", False, "Unexpected response format", str(data))
        else:
            self.log_result("Health Check", False, f"Status code: {response.status_code}", response.text)
        
        return False
    
    def test_locations_endpoint(self):
        """Test Tamil Nadu locations endpoint"""
        print("\n🔍 Testing Locations Endpoint...")
        
        response, error = self.make_request("GET", "/locations")
        if error:
            self.log_result("Locations Endpoint", False, "Request failed", error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            # Check if Tamil Nadu districts are present
            expected_districts = ["Chennai", "Coimbatore", "Madurai"]
            if all(district in data for district in expected_districts):
                self.log_result("Locations Endpoint", True, "Tamil Nadu location data available")
                return True
            else:
                self.log_result("Locations Endpoint", False, "Missing expected districts", str(data.keys()))
        else:
            self.log_result("Locations Endpoint", False, f"Status code: {response.status_code}", response.text)
        
        return False
    
    def test_user_registration(self):
        """Test user registration for all 3 user types"""
        print("\n🔍 Testing User Registration...")
        
        user_types = [
            {
                "type": "customer",
                "email": "priya.customer@orderbuddy.com",
                "name": "Priya Sharma",
                "phone": "+91-9876543210",
                "district": "Chennai",
                "taluk": "Chennai North",
                "village_city": "Washermanpet"
            },
            {
                "type": "shop_owner",
                "email": "ravi.shopowner@orderbuddy.com", 
                "name": "Ravi Kumar",
                "phone": "+91-9876543211",
                "district": "Coimbatore",
                "taluk": "Coimbatore South",
                "village_city": "Singanallur"
            },
            {
                "type": "delivery_person",
                "email": "kumar.delivery@orderbuddy.com",
                "name": "Kumar Raj",
                "phone": "+91-9876543212",
                "district": "Madurai",
                "taluk": "Melur",
                "village_city": "Melur"
            }
        ]
        
        success_count = 0
        for user_data in user_types:
            user_payload = {
                "email": user_data["email"],
                "password": "SecurePass123!",
                "name": user_data["name"],
                "phone": user_data["phone"],
                "user_type": user_data["type"],
                "district": user_data["district"],
                "taluk": user_data["taluk"],
                "village_city": user_data["village_city"]
            }
            
            response, error = self.make_request("POST", "/auth/register", user_payload)
            if error:
                self.log_result(f"Register {user_data['type']}", False, "Request failed", error)
                continue
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.test_users[user_data["type"]] = {
                        "user_data": data["user"],
                        "token": data["token"],
                        "email": user_data["email"],
                        "password": "SecurePass123!"
                    }
                    self.log_result(f"Register {user_data['type']}", True, f"User {user_data['name']} registered successfully")
                    success_count += 1
                else:
                    self.log_result(f"Register {user_data['type']}", False, "Missing token or user in response", str(data))
            else:
                self.log_result(f"Register {user_data['type']}", False, f"Status code: {response.status_code}", response.text)
        
        return success_count == len(user_types)
    
    def test_user_login(self):
        """Test user login for all registered users"""
        print("\n🔍 Testing User Login...")
        
        success_count = 0
        for user_type, user_info in self.test_users.items():
            login_payload = {
                "email": user_info["email"],
                "password": user_info["password"]
            }
            
            response, error = self.make_request("POST", "/auth/login", login_payload)
            if error:
                self.log_result(f"Login {user_type}", False, "Request failed", error)
                continue
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    # Update token (in case it's different)
                    self.test_users[user_type]["token"] = data["token"]
                    self.log_result(f"Login {user_type}", True, f"Login successful for {user_info['email']}")
                    success_count += 1
                else:
                    self.log_result(f"Login {user_type}", False, "Missing token or user in response", str(data))
            else:
                self.log_result(f"Login {user_type}", False, f"Status code: {response.status_code}", response.text)
        
        return success_count == len(self.test_users)
    
    def test_shop_creation(self):
        """Test shop creation by shop owner"""
        print("\n🔍 Testing Shop Creation...")
        
        if "shop_owner" not in self.test_users:
            self.log_result("Shop Creation", False, "No shop owner user available", "")
            return False
        
        shop_owner = self.test_users["shop_owner"]
        shop_payload = {
            "name": "Ravi's General Store",
            "description": "Fresh groceries and daily essentials in Coimbatore",
            "district": "Coimbatore",
            "taluk": "Coimbatore South",
            "village_city": "Singanallur",
            "opening_time": "08:00",
            "closing_time": "22:00"
        }
        
        response, error = self.make_request("POST", "/shops", shop_payload, token=shop_owner["token"])
        if error:
            self.log_result("Shop Creation", False, "Request failed", error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            if "shop" in data:
                self.test_shops["general_store"] = data["shop"]
                self.log_result("Shop Creation", True, f"Shop '{shop_payload['name']}' created successfully")
                return True
            else:
                self.log_result("Shop Creation", False, "Missing shop in response", str(data))
        else:
            self.log_result("Shop Creation", False, f"Status code: {response.status_code}", response.text)
        
        return False
    
    def test_product_creation(self):
        """Test product creation in shop"""
        print("\n🔍 Testing Product Creation...")
        
        if "shop_owner" not in self.test_users or "general_store" not in self.test_shops:
            self.log_result("Product Creation", False, "No shop owner or shop available", "")
            return False
        
        shop_owner = self.test_users["shop_owner"]
        shop = self.test_shops["general_store"]
        
        products = [
            {
                "name": "Basmati Rice",
                "description": "Premium quality basmati rice - 1kg pack",
                "price": 120.0,
                "category": "Groceries",
                "stock_quantity": 50,
                "image_url": "https://example.com/rice.jpg"
            },
            {
                "name": "Fresh Tomatoes",
                "description": "Farm fresh tomatoes - per kg",
                "price": 40.0,
                "category": "Vegetables",
                "stock_quantity": 25,
                "image_url": "https://example.com/tomatoes.jpg"
            }
        ]
        
        success_count = 0
        for product_data in products:
            response, error = self.make_request("POST", f"/shops/{shop['id']}/products", product_data, token=shop_owner["token"])
            if error:
                self.log_result(f"Create Product {product_data['name']}", False, "Request failed", error)
                continue
            
            if response.status_code == 200:
                data = response.json()
                if "product" in data:
                    self.test_products[product_data["name"]] = data["product"]
                    self.log_result(f"Create Product {product_data['name']}", True, f"Product created successfully")
                    success_count += 1
                else:
                    self.log_result(f"Create Product {product_data['name']}", False, "Missing product in response", str(data))
            else:
                self.log_result(f"Create Product {product_data['name']}", False, f"Status code: {response.status_code}", response.text)
        
        return success_count == len(products)
    
    def test_shop_listing(self):
        """Test shop listing with location filtering"""
        print("\n🔍 Testing Shop Listing...")
        
        # Test general shop listing
        response, error = self.make_request("GET", "/shops")
        if error:
            self.log_result("Shop Listing", False, "Request failed", error)
            return False
        
        if response.status_code == 200:
            shops = response.json()
            if isinstance(shops, list) and len(shops) > 0:
                self.log_result("Shop Listing", True, f"Found {len(shops)} shops")
            else:
                self.log_result("Shop Listing", False, "No shops found", str(shops))
                return False
        else:
            self.log_result("Shop Listing", False, f"Status code: {response.status_code}", response.text)
            return False
        
        # Test location-based filtering
        response, error = self.make_request("GET", "/shops", {"district": "Coimbatore"})
        if error:
            self.log_result("Shop Location Filter", False, "Request failed", error)
            return False
        
        if response.status_code == 200:
            filtered_shops = response.json()
            if isinstance(filtered_shops, list):
                self.log_result("Shop Location Filter", True, f"Found {len(filtered_shops)} shops in Coimbatore")
                return True
            else:
                self.log_result("Shop Location Filter", False, "Invalid response format", str(filtered_shops))
        else:
            self.log_result("Shop Location Filter", False, f"Status code: {response.status_code}", response.text)
        
        return False
    
    def test_product_search(self):
        """Test product search functionality"""
        print("\n🔍 Testing Product Search...")
        
        # Test general product search
        response, error = self.make_request("GET", "/products/search", {"query": "rice"})
        if error:
            self.log_result("Product Search", False, "Request failed", error)
            return False
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                self.log_result("Product Search", True, f"Found {len(products)} products for 'rice'")
            else:
                self.log_result("Product Search", False, "Invalid response format", str(products))
                return False
        else:
            self.log_result("Product Search", False, f"Status code: {response.status_code}", response.text)
            return False
        
        # Test location-based product search
        response, error = self.make_request("GET", "/products/search", {"district": "Coimbatore", "category": "Groceries"})
        if error:
            self.log_result("Product Location Search", False, "Request failed", error)
            return False
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                self.log_result("Product Location Search", True, f"Found {len(products)} grocery products in Coimbatore")
                return True
            else:
                self.log_result("Product Location Search", False, "Invalid response format", str(products))
        else:
            self.log_result("Product Location Search", False, f"Status code: {response.status_code}", response.text)
        
        return False
    
    def test_cart_operations(self):
        """Test shopping cart operations"""
        print("\n🔍 Testing Cart Operations...")
        
        if "customer" not in self.test_users or not self.test_products:
            self.log_result("Cart Operations", False, "No customer user or products available", "")
            return False
        
        customer = self.test_users["customer"]
        
        # Add items to cart
        success_count = 0
        for product_name, product in self.test_products.items():
            cart_item = {
                "product_id": product["id"],
                "quantity": 2
            }
            
            response, error = self.make_request("POST", "/cart", cart_item, token=customer["token"])
            if error:
                self.log_result(f"Add to Cart {product_name}", False, "Request failed", error)
                continue
            
            if response.status_code == 200:
                self.log_result(f"Add to Cart {product_name}", True, "Item added to cart")
                success_count += 1
            else:
                self.log_result(f"Add to Cart {product_name}", False, f"Status code: {response.status_code}", response.text)
        
        # Get cart contents
        response, error = self.make_request("GET", "/cart", token=customer["token"])
        if error:
            self.log_result("Get Cart", False, "Request failed", error)
            return False
        
        if response.status_code == 200:
            cart_items = response.json()
            if isinstance(cart_items, list) and len(cart_items) > 0:
                self.log_result("Get Cart", True, f"Cart contains {len(cart_items)} items")
                return success_count > 0
            else:
                self.log_result("Get Cart", False, "Cart is empty or invalid format", str(cart_items))
        else:
            self.log_result("Get Cart", False, f"Status code: {response.status_code}", response.text)
        
        return False
    
    def test_order_placement(self):
        """Test order placement"""
        print("\n🔍 Testing Order Placement...")
        
        if "customer" not in self.test_users or "general_store" not in self.test_shops or not self.test_products:
            self.log_result("Order Placement", False, "Missing required data", "")
            return False
        
        customer = self.test_users["customer"]
        shop = self.test_shops["general_store"]
        
        # Prepare order items
        order_items = []
        total_amount = 0
        for product_name, product in self.test_products.items():
            quantity = 1
            item = {
                "product_id": product["id"],
                "quantity": quantity,
                "price": product["price"],
                "name": product["name"]
            }
            order_items.append(item)
            total_amount += product["price"] * quantity
        
        order_payload = {
            "shop_id": shop["id"],
            "items": order_items,
            "total_amount": total_amount,
            "delivery_address": "123 Main Street, Washermanpet, Chennai North, Chennai"
        }
        
        response, error = self.make_request("POST", "/orders", order_payload, token=customer["token"])
        if error:
            self.log_result("Order Placement", False, "Request failed", error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            if "order" in data:
                self.test_orders["customer_order"] = data["order"]
                self.log_result("Order Placement", True, f"Order placed successfully with total ₹{total_amount}")
                return True
            else:
                self.log_result("Order Placement", False, "Missing order in response", str(data))
        else:
            self.log_result("Order Placement", False, f"Status code: {response.status_code}", response.text)
        
        return False
    
    def test_order_management(self):
        """Test order listing and status updates"""
        print("\n🔍 Testing Order Management...")
        
        success_count = 0
        
        # Test customer order listing
        if "customer" in self.test_users:
            customer = self.test_users["customer"]
            response, error = self.make_request("GET", "/orders", token=customer["token"])
            if error:
                self.log_result("Customer Order List", False, "Request failed", error)
            elif response.status_code == 200:
                orders = response.json()
                if isinstance(orders, list):
                    self.log_result("Customer Order List", True, f"Customer has {len(orders)} orders")
                    success_count += 1
                else:
                    self.log_result("Customer Order List", False, "Invalid response format", str(orders))
            else:
                self.log_result("Customer Order List", False, f"Status code: {response.status_code}", response.text)
        
        # Test shop owner order listing
        if "shop_owner" in self.test_users:
            shop_owner = self.test_users["shop_owner"]
            response, error = self.make_request("GET", "/orders", token=shop_owner["token"])
            if error:
                self.log_result("Shop Owner Order List", False, "Request failed", error)
            elif response.status_code == 200:
                orders = response.json()
                if isinstance(orders, list):
                    self.log_result("Shop Owner Order List", True, f"Shop owner has {len(orders)} orders")
                    success_count += 1
                else:
                    self.log_result("Shop Owner Order List", False, "Invalid response format", str(orders))
            else:
                self.log_result("Shop Owner Order List", False, f"Status code: {response.status_code}", response.text)
        
        # Test order status update
        if "shop_owner" in self.test_users and "customer_order" in self.test_orders:
            shop_owner = self.test_users["shop_owner"]
            order = self.test_orders["customer_order"]
            
            response, error = self.make_request("PATCH", f"/orders/{order['id']}/status", {"status": "packed"}, token=shop_owner["token"])
            if error:
                self.log_result("Order Status Update", False, "Request failed", error)
            elif response.status_code == 200:
                self.log_result("Order Status Update", True, "Order status updated to 'packed'")
                success_count += 1
            else:
                self.log_result("Order Status Update", False, f"Status code: {response.status_code}", response.text)
        
        return success_count >= 2
    
    def test_ai_assistant(self):
        """Test AI shopping assistant"""
        print("\n🔍 Testing AI Assistant...")
        
        if "customer" not in self.test_users:
            self.log_result("AI Assistant", False, "No customer user available", "")
            return False
        
        customer = self.test_users["customer"]
        ai_request = {
            "message": "I need recommendations for fresh vegetables in my area",
            "user_id": customer["user_data"]["id"],
            "context": "product_search"
        }
        
        response, error = self.make_request("POST", "/ai/assistant", ai_request, token=customer["token"])
        if error:
            self.log_result("AI Assistant", False, "Request failed", error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data and data["response"]:
                self.log_result("AI Assistant", True, "AI assistant provided response")
                return True
            else:
                self.log_result("AI Assistant", False, "Empty or missing AI response", str(data))
        else:
            self.log_result("AI Assistant", False, f"Status code: {response.status_code}", response.text)
        
        return False
    
    def test_dashboard_stats(self):
        """Test dashboard statistics for all user types"""
        print("\n🔍 Testing Dashboard Statistics...")
        
        success_count = 0
        
        for user_type, user_info in self.test_users.items():
            response, error = self.make_request("GET", "/dashboard/stats", token=user_info["token"])
            if error:
                self.log_result(f"Dashboard Stats {user_type}", False, "Request failed", error)
                continue
            
            if response.status_code == 200:
                stats = response.json()
                if isinstance(stats, dict) and "user_type" in stats:
                    expected_fields = {
                        "customer": ["total_orders", "cart_items"],
                        "shop_owner": ["total_shops", "total_products", "total_orders"],
                        "delivery_person": ["total_deliveries", "pending_deliveries"]
                    }
                    
                    if user_type in expected_fields:
                        required_fields = expected_fields[user_type]
                        if all(field in stats for field in required_fields):
                            self.log_result(f"Dashboard Stats {user_type}", True, f"Stats retrieved: {stats}")
                            success_count += 1
                        else:
                            missing_fields = [f for f in required_fields if f not in stats]
                            self.log_result(f"Dashboard Stats {user_type}", False, f"Missing fields: {missing_fields}", str(stats))
                    else:
                        self.log_result(f"Dashboard Stats {user_type}", False, "Unknown user type", str(stats))
                else:
                    self.log_result(f"Dashboard Stats {user_type}", False, "Invalid response format", str(stats))
            else:
                self.log_result(f"Dashboard Stats {user_type}", False, f"Status code: {response.status_code}", response.text)
        
        return success_count == len(self.test_users)
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting OrderBuddy Backend API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test sequence
        test_functions = [
            self.test_health_check,
            self.test_locations_endpoint,
            self.test_user_registration,
            self.test_user_login,
            self.test_shop_creation,
            self.test_product_creation,
            self.test_shop_listing,
            self.test_product_search,
            self.test_cart_operations,
            self.test_order_placement,
            self.test_order_management,
            self.test_ai_assistant,
            self.test_dashboard_stats
        ]
        
        for test_func in test_functions:
            try:
                test_func()
            except Exception as e:
                self.log_result(test_func.__name__, False, "Test execution failed", str(e))
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"✅ Passed: {self.results['passed_tests']}")
        print(f"❌ Failed: {self.results['failed_tests']}")
        print(f"Success Rate: {(self.results['passed_tests']/self.results['total_tests']*100):.1f}%")
        
        if self.results['errors']:
            print("\n🔍 FAILED TESTS DETAILS:")
            for error in self.results['errors']:
                print(f"  • {error}")
        
        return self.results

if __name__ == "__main__":
    tester = OrderBuddyTester()
    results = tester.run_all_tests()