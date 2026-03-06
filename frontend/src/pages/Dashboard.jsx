import { useAuth } from '../auth/useAuth';

const Dashboard = () => {
  const { user } = useAuth();

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Welcome to PostPilot AI</h1>
      
      <div style={styles.card}>
        <h2 style={styles.cardTitle}>Account Information</h2>
        <div style={styles.info}>
          <div style={styles.infoRow}>
            <span style={styles.label}>Email:</span>
            <span style={styles.value}>{user?.email}</span>
          </div>
          <div style={styles.infoRow}>
            <span style={styles.label}>Instagram Connected:</span>
            <span style={styles.value}>
              {user?.instagram_connected ? `Yes (@${user.instagram_username})` : 'No'}
            </span>
          </div>
          <div style={styles.infoRow}>
            <span style={styles.label}>Daily Campaign Quota:</span>
            <span style={styles.value}>
              {user?.campaigns_generated_today || 0} / {user?.daily_campaign_quota || 50}
            </span>
          </div>
        </div>
      </div>

      <div style={styles.grid}>
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Products</h3>
          <p style={styles.cardText}>
            Upload and manage your products to generate AI-powered campaigns.
          </p>
        </div>

        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Campaigns</h3>
          <p style={styles.cardText}>
            Generate, schedule, and manage your Instagram campaigns.
          </p>
        </div>

        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Analytics</h3>
          <p style={styles.cardText}>
            View performance metrics and insights for your published campaigns.
          </p>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    padding: '1rem',
  },
  title: {
    fontSize: '2rem',
    color: '#333',
    marginBottom: '2rem',
  },
  card: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    marginBottom: '2rem',
  },
  cardTitle: {
    fontSize: '1.25rem',
    color: '#333',
    marginBottom: '1rem',
  },
  cardText: {
    color: '#666',
    lineHeight: '1.6',
  },
  info: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  infoRow: {
    display: 'flex',
    gap: '1rem',
  },
  label: {
    fontWeight: '600',
    color: '#333',
    minWidth: '180px',
  },
  value: {
    color: '#666',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '1.5rem',
  },
};

export default Dashboard;
