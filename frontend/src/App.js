import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { user, token } = response.data;
      setUser(user);
      setToken(token);
      localStorage.setItem('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      return { success: true, user };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      const { user, token } = response.data;
      setUser(user);
      setToken(token);
      localStorage.setItem('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      return { success: true, user };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Components
const Navbar = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-gradient-to-r from-blue-600 to-purple-600 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🤖</div>
            <h1 className="text-white text-xl font-bold">OrderBuddy</h1>
            <span className="text-blue-200 text-sm">Tamil Nadu's Smart Shopping Platform</span>
          </div>
          {user && (
            <div className="flex items-center space-x-4">
              <span className="text-white">Welcome, {user.name}!</span>
              <span className="text-blue-200 text-sm">({user.user_type})</span>
              <button
                onClick={logout}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

const LocationSelector = ({ onLocationChange, selectedLocation = {} }) => {
  const [locations, setLocations] = useState({});

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const response = await axios.get(`${API}/locations`);
        setLocations(response.data);
      } catch (error) {
        console.error('Failed to fetch locations:', error);
      }
    };
    fetchLocations();
  }, []);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">District</label>
        <select
          value={selectedLocation.district || ''}
          onChange={(e) => onLocationChange({ ...selectedLocation, district: e.target.value, taluk: '', village_city: '' })}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
        >
          <option value="">Select District</option>
          {Object.keys(locations).map(district => (
            <option key={district} value={district}>{district}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Taluk</label>
        <select
          value={selectedLocation.taluk || ''}
          onChange={(e) => onLocationChange({ ...selectedLocation, taluk: e.target.value, village_city: '' })}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
          disabled={!selectedLocation.district}
        >
          <option value="">Select Taluk</option>
          {selectedLocation.district && locations[selectedLocation.district] && 
           Object.keys(locations[selectedLocation.district].taluks).map(taluk => (
            <option key={taluk} value={taluk}>{taluk}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Village/City</label>
        <select
          value={selectedLocation.village_city || ''}
          onChange={(e) => onLocationChange({ ...selectedLocation, village_city: e.target.value })}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
          disabled={!selectedLocation.taluk}
        >
          <option value="">Select Village/City</option>
          {selectedLocation.district && selectedLocation.taluk && 
           locations[selectedLocation.district]?.taluks[selectedLocation.taluk]?.map(village => (
            <option key={village} value={village}>{village}</option>
          ))}
        </select>
      </div>
    </div>
  );
};

const LoginForm = ({ onToggle }) => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await login(formData.email, formData.password);
    if (!result.success) {
      setError(result.error);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center max-w-6xl mx-auto p-8">
      {/* Left side - Beautiful Tamil Nadu shopping images */}
      <div className="hidden lg:block">
        <div className="relative">
          <img 
            src="https://images.unsplash.com/photo-1666856573860-cb7cd88992b3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzl8MHwxfHNlYXJjaHwxfHxUYW1pbCUyME5hZHUlMjBzaG9wc3xlbnwwfHx8fDE3NTk4NDQ2MTl8MA&ixlib=rb-4.1.0&q=85"
            alt="Tamil Nadu Local Market"
            className="w-full h-96 object-cover rounded-2xl shadow-xl"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent rounded-2xl"></div>
          <div className="absolute bottom-6 left-6 text-white">
            <h3 className="text-2xl font-bold mb-2">Fresh Local Markets</h3>
            <p className="text-lg opacity-90">Discover authentic Tamil Nadu shopping experience</p>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mt-6">
          <img 
            src="https://images.unsplash.com/photo-1588964895597-cfccd6e2dbf9?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwxfHxncm9jZXJ5JTIwZGVsaXZlcnl8ZW58MHx8fHwxNzU5ODQ0NjI1fDA&ixlib=rb-4.1.0&q=85"
            alt="Grocery Delivery"
            className="w-full h-32 object-cover rounded-xl"
          />
          <img 
            src="https://images.unsplash.com/photo-1757802868665-60b771aa399b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwxfHxJbmRpYW4lMjBncm9jZXJ5fGVufDB8fHx8MTc1OTg0NDYzMnww&ixlib=rb-4.1.0&q=85"
            alt="Indian Grocery Products"
            className="w-full h-32 object-cover rounded-xl"
          />
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="max-w-md mx-auto bg-white rounded-xl shadow-2xl p-8">
        <div className="text-center mb-6">
          <div className="text-4xl mb-2 animate-bounce">🤖</div>
          <h2 className="text-2xl font-bold text-gray-800">Welcome Back!</h2>
          <p className="text-gray-600">Sign in to OrderBuddy</p>
          <p className="text-sm text-blue-600 mt-2">Your Tamil Nadu Shopping Companion</p>
        </div>

        {/* Demo credentials */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-sm font-semibold text-blue-800 mb-2">Try Demo Accounts:</p>
          <div className="space-y-1 text-xs text-blue-700">
            <p><strong>Customer:</strong> priya@customer.com / password123</p>
            <p><strong>Shop Owner:</strong> ravi@shop.com / password123</p>
            <p><strong>Delivery:</strong> kumar@delivery.com / password123</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 font-semibold transform hover:scale-105"
          >
            Sign In
          </button>
        </form>

        <div className="text-center mt-6">
          <p className="text-gray-600">
            Don't have an account?{' '}
            <button
              onClick={onToggle}
              className="text-blue-600 hover:text-blue-700 font-semibold"
            >
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

const RegisterForm = ({ onToggle }) => {
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    phone: '',
    user_type: 'customer',
    district: '',
    taluk: '',
    village_city: ''
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await register(formData);
    if (!result.success) {
      setError(result.error);
    }
  };

  const handleLocationChange = (location) => {
    setFormData({ ...formData, ...location });
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-lg p-8">
      <div className="text-center mb-6">
        <div className="text-4xl mb-2">🤖</div>
        <h2 className="text-2xl font-bold text-gray-800">Join OrderBuddy!</h2>
        <p className="text-gray-600">Create your account</p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">User Type</label>
          <select
            value={formData.user_type}
            onChange={(e) => setFormData({ ...formData, user_type: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          >
            <option value="customer">🛒 Customer</option>
            <option value="shop_owner">🏪 Shop Owner</option>
            <option value="delivery_person">🚚 Delivery Person</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
          <LocationSelector onLocationChange={handleLocationChange} selectedLocation={formData} />
        </div>

        <button
          type="submit"
          className="w-full bg-gradient-to-r from-green-500 to-blue-600 text-white py-3 rounded-lg hover:from-green-600 hover:to-blue-700 transition-all duration-200 font-semibold"
        >
          Create Account
        </button>
      </form>

      <div className="text-center mt-6">
        <p className="text-gray-600">
          Already have an account?{' '}
          <button
            onClick={onToggle}
            className="text-blue-600 hover:text-blue-700 font-semibold"
          >
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
};

const CustomerDashboard = () => {
  const { user } = useAuth();
  const [shops, setShops] = useState([]);
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('shops');
  const [orders, setOrders] = useState([]);
  const [aiResponse, setAiResponse] = useState('');
  const [aiMessage, setAiMessage] = useState('');

  useEffect(() => {
    fetchShops();
    fetchCart();
    fetchOrders();
  }, []);

  const fetchShops = async () => {
    try {
      const response = await axios.get(`${API}/shops`, {
        params: {
          district: user.district,
          taluk: user.taluk,
          village_city: user.village_city
        }
      });
      setShops(response.data);
    } catch (error) {
      console.error('Failed to fetch shops:', error);
    }
  };

  const fetchProducts = async (shopId) => {
    try {
      const response = await axios.get(`${API}/shops/${shopId}/products`);
      setProducts(response.data);
      setActiveTab('products');
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  const fetchCart = async () => {
    try {
      const response = await axios.get(`${API}/cart`);
      setCart(response.data);
    } catch (error) {
      console.error('Failed to fetch cart:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    }
  };

  const addToCart = async (productId, quantity = 1) => {
    try {
      await axios.post(`${API}/cart`, { product_id: productId, quantity });
      fetchCart();
      alert('Product added to cart!');
    } catch (error) {
      console.error('Failed to add to cart:', error);
      alert('Failed to add product to cart');
    }
  };

  const placeOrder = async () => {
    if (cart.length === 0) {
      alert('Cart is empty!');
      return;
    }

    const shopId = cart[0].product.shop_id;
    const items = cart.map(item => ({
      product_id: item.product_id,
      quantity: item.quantity,
      price: item.product.price,
      name: item.product.name
    }));
    const totalAmount = cart.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);

    try {
      await axios.post(`${API}/orders`, {
        shop_id: shopId,
        items,
        total_amount: totalAmount,
        delivery_address: `${user.village_city}, ${user.taluk}, ${user.district}`
      });
      fetchCart();
      fetchOrders();
      setActiveTab('orders');
      alert('Order placed successfully!');
    } catch (error) {
      console.error('Failed to place order:', error);
      alert('Failed to place order');
    }
  };

  const askAI = async () => {
    if (!aiMessage.trim()) return;

    try {
      const response = await axios.post(`${API}/ai/assistant`, {
        message: aiMessage,
        user_id: user.id,
        context: 'product_search'
      });
      setAiResponse(response.data.response);
      setAiMessage('');
    } catch (error) {
      console.error('AI Assistant failed:', error);
      setAiResponse('Sorry, I am currently unavailable. Please try again later.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          Welcome to OrderBuddy, {user.name}! 🛒
        </h1>
        <p className="text-gray-600">
          Shopping in {user.village_city}, {user.taluk}, {user.district}
        </p>
      </div>

      {/* AI Assistant Section */}
      <div className="bg-gradient-to-r from-purple-100 to-blue-100 rounded-xl p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          🤖 AI Shopping Assistant
        </h2>
        <div className="flex space-x-4 mb-4">
          <input
            type="text"
            value={aiMessage}
            onChange={(e) => setAiMessage(e.target.value)}
            placeholder="Ask me anything about products, shops, or orders..."
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            onKeyPress={(e) => e.key === 'Enter' && askAI()}
          />
          <button
            onClick={askAI}
            className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors"
          >
            Ask AI
          </button>
        </div>
        {aiResponse && (
          <div className="bg-white p-4 rounded-lg border-l-4 border-purple-500">
            <p className="text-gray-800">{aiResponse}</p>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-4 mb-6">
        {['shops', 'products', 'cart', 'orders'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg capitalize font-medium ${
              activeTab === tab
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {tab} {tab === 'cart' && cart.length > 0 && `(${cart.length})`}
          </button>
        ))}
      </div>

      {/* Content Based on Active Tab */}
      {activeTab === 'shops' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {shops.map(shop => (
            <div key={shop.id} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-gray-800">{shop.name}</h3>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  shop.is_open ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {shop.is_open ? 'Open' : 'Closed'}
                </span>
              </div>
              <p className="text-gray-600 mb-4">{shop.description}</p>
              <p className="text-sm text-gray-500 mb-4">
                📍 {shop.village_city}, {shop.taluk}
              </p>
              <button
                onClick={() => fetchProducts(shop.id)}
                className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                View Products
              </button>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'products' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map(product => (
            <div key={product.id} className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-2">{product.name}</h3>
              <p className="text-gray-600 mb-3">{product.description}</p>
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl font-bold text-green-600">₹{product.price}</span>
                <span className="text-sm text-gray-500">Stock: {product.stock_quantity}</span>
              </div>
              <button
                onClick={() => addToCart(product.id)}
                disabled={product.stock_quantity === 0}
                className={`w-full py-2 rounded-lg transition-colors ${
                  product.stock_quantity > 0
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {product.stock_quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
              </button>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'cart' && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-semibold mb-6">Shopping Cart</h2>
          {cart.length === 0 ? (
            <p className="text-gray-500 text-center py-8">Your cart is empty</p>
          ) : (
            <>
              {cart.map(item => (
                <div key={item.id} className="flex items-center justify-between border-b py-4">
                  <div>
                    <h3 className="font-semibold">{item.product.name}</h3>
                    <p className="text-gray-600">Quantity: {item.quantity}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">₹{item.product.price * item.quantity}</p>
                  </div>
                </div>
              ))}
              <div className="mt-6 flex justify-between items-center">
                <div>
                  <p className="text-xl font-bold">
                    Total: ₹{cart.reduce((sum, item) => sum + (item.product.price * item.quantity), 0)}
                  </p>
                </div>
                <button
                  onClick={placeOrder}
                  className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Place Order
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === 'orders' && (
        <div className="space-y-4">
          {orders.map(order => (
            <div key={order.id} className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">Order #{order.id.slice(-8)}</h3>
                  <p className="text-gray-600">Total: ₹{order.total_amount}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm capitalize ${
                  order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                  order.status === 'on_the_way' ? 'bg-blue-100 text-blue-800' :
                  order.status === 'packed' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {order.status.replace('_', ' ')}
                </span>
              </div>
              <div className="border-t pt-4">
                {order.items.map((item, index) => (
                  <div key={index} className="flex justify-between py-1">
                    <span>{item.name} x{item.quantity}</span>
                    <span>₹{item.price * item.quantity}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const ShopOwnerDashboard = () => {
  const { user } = useAuth();
  const [shops, setShops] = useState([]);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [activeTab, setActiveTab] = useState('shops');
  const [showCreateShop, setShowCreateShop] = useState(false);
  const [showCreateProduct, setShowCreateProduct] = useState(false);
  const [selectedShop, setSelectedShop] = useState(null);

  useEffect(() => {
    fetchShops();
    fetchOrders();
  }, []);

  const fetchShops = async () => {
    try {
      const response = await axios.get(`${API}/shops/my`);
      setShops(response.data);
    } catch (error) {
      console.error('Failed to fetch shops:', error);
    }
  };

  const fetchProducts = async (shopId) => {
    try {
      const response = await axios.get(`${API}/shops/${shopId}/products`);
      setProducts(response.data);
      setSelectedShop(shopId);
      setActiveTab('products');
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.patch(`${API}/orders/${orderId}/status?status=${status}`);
      fetchOrders();
      alert('Order status updated successfully!');
    } catch (error) {
      console.error('Failed to update order status:', error);
      alert('Failed to update order status');
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          Shop Owner Dashboard 🏪
        </h1>
        <p className="text-gray-600">
          Manage your business in {user.village_city}, {user.taluk}, {user.district}
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-4 mb-6">
        {['shops', 'products', 'orders'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg capitalize font-medium ${
              activeTab === tab
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Shop Management */}
      {activeTab === 'shops' && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">Your Shops</h2>
            <button
              onClick={() => setShowCreateShop(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              + Add New Shop
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {shops.map(shop => (
              <div key={shop.id} className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-2">{shop.name}</h3>
                <p className="text-gray-600 mb-4">{shop.description}</p>
                <div className="flex justify-between items-center">
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    shop.is_open ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {shop.is_open ? 'Open' : 'Closed'}
                  </span>
                  <button
                    onClick={() => fetchProducts(shop.id)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Manage Products
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Create Shop Modal */}
          {showCreateShop && (
            <CreateShopModal
              onClose={() => setShowCreateShop(false)}
              onSuccess={() => {
                fetchShops();
                setShowCreateShop(false);
              }}
            />
          )}
        </div>
      )}

      {/* Product Management */}
      {activeTab === 'products' && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">Products</h2>
            {selectedShop && (
              <button
                onClick={() => setShowCreateProduct(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                + Add Product
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map(product => (
              <div key={product.id} className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-2">{product.name}</h3>
                <p className="text-gray-600 mb-3">{product.description}</p>
                <div className="flex justify-between items-center">
                  <span className="text-2xl font-bold text-green-600">₹{product.price}</span>
                  <span className="text-sm text-gray-500">Stock: {product.stock_quantity}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Create Product Modal */}
          {showCreateProduct && selectedShop && (
            <CreateProductModal
              shopId={selectedShop}
              onClose={() => setShowCreateProduct(false)}
              onSuccess={() => {
                fetchProducts(selectedShop);
                setShowCreateProduct(false);
              }}
            />
          )}
        </div>
      )}

      {/* Order Management */}
      {activeTab === 'orders' && (
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold mb-6">Orders</h2>
          {orders.map(order => (
            <div key={order.id} className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">Order #{order.id.slice(-8)}</h3>
                  <p className="text-gray-600">Total: ₹{order.total_amount}</p>
                </div>
                <div className="flex space-x-2">
                  {order.status !== 'delivered' && (
                    <>
                      {order.status === 'pending' && (
                        <button
                          onClick={() => updateOrderStatus(order.id, 'packed')}
                          className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                        >
                          Mark Packed
                        </button>
                      )}
                      {order.status === 'packed' && (
                        <button
                          onClick={() => updateOrderStatus(order.id, 'on_the_way')}
                          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                        >
                          Out for Delivery
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm capitalize ${
                order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                order.status === 'on_the_way' ? 'bg-blue-100 text-blue-800' :
                order.status === 'packed' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {order.status.replace('_', ' ')}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const CreateShopModal = ({ onClose, onSuccess }) => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    district: user.district,
    taluk: user.taluk,
    village_city: user.village_city
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/shops`, formData);
      onSuccess();
    } catch (error) {
      console.error('Failed to create shop:', error);
      alert('Failed to create shop');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl p-6 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4">Create New Shop</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Shop Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg"
              rows={3}
              required
            />
          </div>
          <div className="flex space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700"
            >
              Create Shop
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const CreateProductModal = ({ shopId, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    stock_quantity: '',
    image_url: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/shops/${shopId}/products`, {
        ...formData,
        price: parseFloat(formData.price),
        stock_quantity: parseInt(formData.stock_quantity)
      });
      onSuccess();
    } catch (error) {
      console.error('Failed to create product:', error);
      alert('Failed to create product');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl p-6 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4">Add New Product</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Product Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg"
              rows={2}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Price (₹)</label>
              <input
                type="number"
                step="0.01"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Stock</label>
              <input
                type="number"
                value={formData.stock_quantity}
                onChange={(e) => setFormData({ ...formData, stock_quantity: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
            <input
              type="text"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
          </div>
          <div className="flex space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700"
            >
              Add Product
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const DeliveryDashboard = () => {
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.patch(`${API}/orders/${orderId}/status?status=${status}`);
      fetchOrders();
      alert('Order status updated successfully!');
    } catch (error) {
      console.error('Failed to update order status:', error);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          Delivery Dashboard 🚚
        </h1>
        <p className="text-gray-600">
          Managing deliveries in {user.village_city}, {user.taluk}, {user.district}
        </p>
      </div>

      <div className="space-y-4">
        {orders.map(order => (
          <div key={order.id} className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold">Order #{order.id.slice(-8)}</h3>
                <p className="text-gray-600">Total: ₹{order.total_amount}</p>
                <p className="text-gray-600">Delivery: {order.delivery_address}</p>
              </div>
              <div className="flex space-x-2">
                {order.status === 'on_the_way' && (
                  <button
                    onClick={() => updateOrderStatus(order.id, 'delivered')}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                  >
                    Mark Delivered
                  </button>
                )}
              </div>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm capitalize ${
              order.status === 'delivered' ? 'bg-green-100 text-green-800' :
              order.status === 'on_the_way' ? 'bg-blue-100 text-blue-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {order.status.replace('_', ' ')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

const App = () => {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <AuthProvider>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
        <AuthenticatedApp isLogin={isLogin} setIsLogin={setIsLogin} />
      </div>
    </AuthProvider>
  );
};

const AuthenticatedApp = ({ isLogin, setIsLogin }) => {
  const { user } = useAuth();

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        {isLogin ? (
          <LoginForm onToggle={() => setIsLogin(false)} />
        ) : (
          <RegisterForm onToggle={() => setIsLogin(true)} />
        )}
      </div>
    );
  }

  return (
    <>
      <Navbar />
      {user.user_type === 'customer' && <CustomerDashboard />}
      {user.user_type === 'shop_owner' && <ShopOwnerDashboard />}
      {user.user_type === 'delivery_person' && <DeliveryDashboard />}
    </>
  );
};

export default App;