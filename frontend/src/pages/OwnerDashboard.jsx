import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../context/AuthContext';

const initialMenuForm = {
  name: '',
  description: '',
  price: '',
  category: 'General',
  is_available: true,
};

export default function OwnerDashboard() {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [restaurant, setRestaurant] = useState(null);
  const [stats, setStats] = useState({ total_orders: 0, delivered_orders: 0, total_revenue: 0 });
  const [reminders, setReminders] = useState([]);
  const [orders, setOrders] = useState([]);
  const [deliveryPartners, setDeliveryPartners] = useState([]);
  const [menuForm, setMenuForm] = useState(initialMenuForm);

  const loadDashboard = async () => {
    try {
      const restaurantResponse = await api.get('/api/restaurants/my-restaurant');
      const statsResponse = await api.get('/api/orders/owner/stats-and-reminders');
      const partnerResponse = await api.get('/api/orders/delivery-partners');
      const ordersResponse = await api.get('/api/orders/');

      setRestaurant(restaurantResponse.data);
      setStats(statsResponse.data.stats || { total_orders: 0, delivered_orders: 0, total_revenue: 0 });
      setReminders(statsResponse.data.reminders || []);
      setDeliveryPartners(partnerResponse.data || []);
      setOrders(ordersResponse.data.items || []);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const updateMenuField = (event) => {
    const { name, value, type, checked } = event.target;
    setMenuForm((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleAddMenuItem = async (event) => {
    event.preventDefault();

    try {
      await api.post('/api/restaurants/menu', {
        ...menuForm,
        price: Number(menuForm.price),
      });
      setMenuForm(initialMenuForm);
      await loadDashboard();
    } catch (error) {
      alert(error.response?.data?.detail || 'Unable to add item');
    }
  };

  const updateStatus = async (orderId, status) => {
    try {
      await api.patch(`/api/orders/${orderId}/status`, { status });
      await loadDashboard();
    } catch (error) {
      alert(error.response?.data?.detail || 'Unable to update status');
    }
  };

  const assignPartner = async (orderId, deliveryPartnerId) => {
    try {
      await api.patch(`/api/orders/${orderId}/assign`, { delivery_partner_id: deliveryPartnerId });
      await loadDashboard();
    } catch (error) {
      alert(error.response?.data?.detail || 'Unable to assign delivery partner');
    }
  };

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="brand">
          <div className="brand-badge">C</div>
          <span>CampusBite Owner</span>
        </div>
        <div className="nav-actions">
          <span>{user?.name}</span>
          <button className="secondary-button" onClick={() => navigate('/login')}>Home</button>
          <button className="primary-button" onClick={logout}>Logout</button>
        </div>
      </nav>

      <div className="dashboard-grid">
        <section className="panel">
          <h2>Restaurant summary</h2>
          <p className="meta">{restaurant?.name || 'No restaurant found yet.'}</p>
          <p className="meta">Location: {restaurant?.location || 'N/A'}</p>

          <div className="stack" style={{ marginTop: '18px' }}>
            <div className="stat-box">Total orders: {stats.total_orders}</div>
            <div className="stat-box">Delivered: {stats.delivered_orders}</div>
            <div className="stat-box">Revenue: ${stats.total_revenue}</div>
          </div>
        </section>

        <section className="panel">
          <h2>Add menu item</h2>
          <form className="form" onSubmit={handleAddMenuItem}>
            <div className="field">
              <label htmlFor="name">Name</label>
              <input id="name" name="name" value={menuForm.name} onChange={updateMenuField} required />
            </div>
            <div className="field">
              <label htmlFor="description">Description</label>
              <input id="description" name="description" value={menuForm.description} onChange={updateMenuField} />
            </div>
            <div className="field">
              <label htmlFor="price">Price</label>
              <input id="price" type="number" name="price" min="0.01" step="0.01" value={menuForm.price} onChange={updateMenuField} required />
            </div>
            <div className="field">
              <label htmlFor="category">Category</label>
              <input id="category" name="category" value={menuForm.category} onChange={updateMenuField} />
            </div>
            <button className="primary-button" type="submit">Add item</button>
          </form>
        </section>
      </div>

      <div className="dashboard-grid" style={{ marginTop: '24px' }}>
        <section className="panel">
          <h2>Orders</h2>
          <div className="list">
            {orders.length === 0 ? (
              <p className="empty-state">No orders yet.</p>
            ) : (
              orders.map((order) => (
                <div className="order-card" key={order.id}>
                  <span className="status-badge">{order.status}</span>
                  <h3>Order #{order.id}</h3>
                  <p className="meta">Customer: {order.customer_id}</p>
                  <p className="meta">Total: ${order.total_amount}</p>
                  <div className="inline-actions">
                    {order.status === 'PLACED' ? <button className="small-button" onClick={() => updateStatus(order.id, 'ACCEPTED')}>Accept</button> : null}
                    {order.status === 'ACCEPTED' ? <button className="small-button" onClick={() => updateStatus(order.id, 'PREPARING')}>Preparing</button> : null}
                    {order.status === 'PREPARING' ? <button className="small-button" onClick={() => updateStatus(order.id, 'READY')}>Ready</button> : null}
                  </div>

                  {deliveryPartners.length > 0 && order.status === 'READY' ? (
                    <div className="inline-actions">
                      {deliveryPartners.map((partner) => (
                        <button className="small-button" key={partner.id} onClick={() => assignPartner(order.id, partner.id)}>
                          Assign {partner.name}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))
            )}
          </div>
        </section>

        <section className="panel">
          <h2>Reminders</h2>
          <div className="list">
            {reminders.length === 0 ? (
              <p className="empty-state">No reminders.</p>
            ) : (
              reminders.map((reminder) => (
                <div className="order-card" key={reminder.id}>
                  <h3>Order #{reminder.order_id}</h3>
                  <p>{reminder.message}</p>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
