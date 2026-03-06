import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <div style={styles.container}>
      <nav style={styles.nav}>
        <div style={styles.navContent}>
          <div style={styles.brand}>
            <h1 style={styles.brandTitle}>PostPilot AI</h1>
          </div>
          
          <div style={styles.navLinks}>
            <Link 
              to="/dashboard" 
              style={{...styles.navLink, ...(isActive('/dashboard') ? styles.navLinkActive : {})}}
            >
              Dashboard
            </Link>
            <Link 
              to="/products" 
              style={{...styles.navLink, ...(isActive('/products') ? styles.navLinkActive : {})}}
            >
              Products
            </Link>
            <Link 
              to="/campaigns" 
              style={{...styles.navLink, ...(isActive('/campaigns') ? styles.navLinkActive : {})}}
            >
              Campaigns
            </Link>
            <Link 
              to="/analytics" 
              style={{...styles.navLink, ...(isActive('/analytics') ? styles.navLinkActive : {})}}
            >
              Analytics
            </Link>
          </div>

          <div style={styles.userSection}>
            <span style={styles.userEmail}>{user?.email}</span>
            <button onClick={handleLogout} style={styles.logoutButton}>
              Logout
            </button>
          </div>
        </div>
      </nav>

      <main style={styles.main}>
        <Outlet />
      </main>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
  },
  nav: {
    backgroundColor: '#fff',
    borderBottom: '1px solid #e0e0e0',
    padding: '1rem 0',
  },
  navContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '2rem',
  },
  brand: {
    marginRight: 'auto',
  },
  brandTitle: {
    fontSize: '1.5rem',
    color: '#333',
    margin: 0,
  },
  navLinks: {
    display: 'flex',
    gap: '1.5rem',
  },
  navLink: {
    color: '#666',
    textDecoration: 'none',
    fontWeight: '500',
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    transition: 'background-color 0.2s',
  },
  navLinkActive: {
    backgroundColor: '#e3f2fd',
    color: '#007bff',
  },
  userSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  userEmail: {
    color: '#666',
    fontSize: '0.9rem',
  },
  logoutButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '500',
  },
  main: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '2rem 1rem',
  },
};

export default DashboardLayout;
