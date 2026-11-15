import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const initialForm = {
  name: '',
  email: '',
  password: '',
  role: 'CUSTOMER',
  address: '',
  restaurant_name: '',
  restaurant_location: '',
};

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = { ...form };
      if (form.role !== 'OWNER') {
        delete payload.restaurant_name;
        delete payload.restaurant_location;
      }
      await register(payload);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to register. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Create account</h1>
          <p>Join CampusBite as a customer, owner, or delivery partner.</p>
        </div>

        <form className="form" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="name">Full name</label>
            <input id="name" name="name" value={form.name} onChange={handleChange} required />
          </div>

          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" value={form.email} onChange={handleChange} required />
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" name="password" type="password" value={form.password} onChange={handleChange} required />
          </div>

          <div className="field">
            <label htmlFor="role">Role</label>
            <select id="role" name="role" value={form.role} onChange={handleChange}>
              <option value="CUSTOMER">Customer</option>
              <option value="OWNER">Owner</option>
              <option value="DELIVERY">Delivery</option>
            </select>
          </div>

          {form.role === 'CUSTOMER' ? (
            <div className="field">
              <label htmlFor="address">Address</label>
              <input id="address" name="address" value={form.address} onChange={handleChange} placeholder="Your delivery address" />
            </div>
          ) : null}

          {form.role === 'OWNER' ? (
            <>
              <div className="field">
                <label htmlFor="restaurant_name">Restaurant name</label>
                <input id="restaurant_name" name="restaurant_name" value={form.restaurant_name} onChange={handleChange} />
              </div>
              <div className="field">
                <label htmlFor="restaurant_location">Restaurant location</label>
                <input id="restaurant_location" name="restaurant_location" value={form.restaurant_location} onChange={handleChange} />
              </div>
            </>
          ) : null}

          {error ? <div className="form-error">{error}</div> : null}

          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="form-link">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
