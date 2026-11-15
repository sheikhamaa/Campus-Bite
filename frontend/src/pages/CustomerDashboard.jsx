import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../context/AuthContext';

export default function CustomerDashboard() {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [restaurants, setRestaurants] = useState([]);
  const [orders, setOrders] = useState([]);
  const [aiQuestion, setAiQuestion] = useState('What is my most ordered dish?');
  const [aiAnswer, setAiAnswer] = useState('');
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const restaurantResponse = await api.get('/api/restaurants/');
      const restaurantsWithMenu = await Promise.all(
        restaurantResponse.data.map(async (restaurant) => {
          const menuResponse = await api.get(`/api/restaurants/${restaurant.id}/menu`);
          return { ...restaurant, menu: menuResponse.data };
        })
      );
      const ordersResponse = await api.get('/api/orders/');

      setRestaurants(restaurantsWithMenu);
      setOrders(ordersResponse.data.items || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const placeOrder = async (restaurantId, menuItemId) => {
    try {
      await api.post('/api/orders/', {
        restaurant_id: restaurantId,
        delivery_address: user?.address || 'Campus Central',
        items: [{ menu_item_id: menuItemId, quantity: 1 }],
      });
      await loadData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Unable to place order');
    }
  };

  const askAi = async () => {
    try {
      const response = await api.post('/api/ai/insights', { question: aiQuestion });
      setAiAnswer(response.data.answer || 'No answer yet.');
    } catch (error) {
      setAiAnswer(error.response?.data?.detail || 'AI service is unavailable right now.');
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="brand">
          <div className="brand-badge">C</div>
          <span>CampusBite</span>
        </div>

        <div className="nav-actions">
          <span>Hello, {user?.name}</span>
          <button className="secondary-button" onClick={() => navigate('/login')}>
            Dashboard
          </button>
          <button className="nav-button primary-button" onClick={logout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="dashboard-grid">
        <section className="panel">
          <h2>Restaurants</h2>
          <div className="list">
            {restaurants.length === 0 ? (
              <p className="empty-state">No restaurants available right now.</p>
            ) : (
              restaurants.map((restaurant) => (
                <div className="restaurant-card" key={restaurant.id}>
                  <h3>{restaurant.name}</h3>
                  <p className="meta">{restaurant.location}</p>
                  <div className="inline-actions">
                    {restaurant.menu && restaurant.menu.length > 0 ? (
                      restaurant.menu.map((item) => (
                        <button
                          className="small-button"
                          key={item.id}
                          onClick={() => placeOrder(restaurant.id, item.id)}
                        >
                          {item.name} - ${item.price}
                        </button>
                      ))
                    ) : (
                      <span className="empty-state">No menu items yet.</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="panel">
          <h2>Your orders</h2>
          <div className="list">
            {orders.length === 0 ? (
              <p className="empty-state">You have not placed any orders yet.</p>
            ) : (
              orders.map((order) => (
                <div className="order-card" key={order.id}>
                  <span className="status-badge">{order.status}</span>
                  <h3>Order #{order.id}</h3>
                  <p className="meta">Restaurant: {order.restaurant_name}</p>
                  <p className="meta">Total: ${order.total_amount}</p>
                  <div className="stack">
                    {order.items?.map((item, index) => (
                      <div key={`${order.id}-${index}`}>
                        {item.name} × {item.quantity}
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <section className="panel" style={{ marginTop: '24px' }}>
        <h2>CampusBite AI</h2>
        <div className="field">
          <label htmlFor="aiQuestion">Ask about your order history</label>
          <input
            id="aiQuestion"
            value={aiQuestion}
            onChange={(event) => setAiQuestion(event.target.value)}
          />
        </div>
        <div className="inline-actions" style={{ marginTop: '12px' }}>
          <button className="primary-button" onClick={askAi}>Ask AI</button>
        </div>
        {aiAnswer ? <p style={{ marginTop: '16px' }}>{aiAnswer}</p> : null}
      </section>
    </div>
  );
}
