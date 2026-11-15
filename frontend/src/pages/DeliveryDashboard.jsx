import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../context/AuthContext';

export default function DeliveryDashboard() {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [orders, setOrders] = useState([]);

  const loadOrders = async () => {
    try {
      const response = await api.get('/api/orders/');
      const deliveries = (response.data.items || []).filter((order) => order.delivery_partner_id === user?.id);
      setOrders(deliveries);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    loadOrders();
  }, [user?.id]);

  const updateStatus = async (orderId, status) => {
    try {
      await api.patch(`/api/orders/${orderId}/status`, { status });
      await loadOrders();
    } catch (error) {
      alert(error.response?.data?.detail || 'Unable to update order status');
    }
  };

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="brand">
          <div className="brand-badge">C</div>
          <span>CampusBite Delivery</span>
        </div>
        <div className="nav-actions">
          <span>{user?.name}</span>
          <button className="secondary-button" onClick={() => navigate('/login')}>Home</button>
          <button className="primary-button" onClick={logout}>Logout</button>
        </div>
      </nav>

      <section className="panel">
        <h2>Assigned deliveries</h2>
        <div className="list">
          {orders.length === 0 ? (
            <p className="empty-state">No deliveries assigned yet.</p>
          ) : (
            orders.map((order) => (
              <div className="order-card" key={order.id}>
                <span className="status-badge">{order.status}</span>
                <h3>Order #{order.id}</h3>
                <p className="meta">Address: {order.delivery_address}</p>
                <p className="meta">Total: ${order.total_amount}</p>
                <div className="inline-actions">
                  {order.status === 'ASSIGNED' ? (
                    <button className="small-button" onClick={() => updateStatus(order.id, 'OUT_FOR_DELIVERY')}>
                      Start delivery
                    </button>
                  ) : null}
                  {order.status === 'OUT_FOR_DELIVERY' ? (
                    <button className="small-button" onClick={() => updateStatus(order.id, 'DELIVERED')}>
                      Mark delivered
                    </button>
                  ) : null}
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
