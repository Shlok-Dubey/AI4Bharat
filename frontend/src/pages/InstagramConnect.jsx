import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { instagramAPI } from '../services/api';
import { useAuth } from '../auth/useAuth';

const InstagramConnect = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    // Check if this is a callback from Instagram
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    
    if (code) {
      handleCallback(code, state);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const handleCallback = async (code, state) => {
    setLoading(true);
    setError('');

    try {
      const response = await instagramAPI.handleCallback(code, state);
      setSuccess(response.data.message);
      
      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to connect Instagram account');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await instagramAPI.getAuthUrl();
      const { authorization_url } = response.data;
      
      // Redirect to Instagram authorization page
      window.location.href = authorization_url;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to initiate Instagram connection');
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Instagram Connection</h1>

        {user?.instagram_connected ? (
          <div style={styles.connected}>
            <div style={styles.successIcon}>✓</div>
            <h2 style={styles.connectedTitle}>Connected</h2>
            <p style={styles.connectedText}>
              Your Instagram account @{user.instagram_username} is connected.
            </p>
            <button onClick={() => navigate('/dashboard')} style={styles.button}>
              Go to Dashboard
            </button>
          </div>
        ) : (
          <>
            {error && <div style={styles.error}>{error}</div>}
            {success && <div style={styles.success}>{success}</div>}

            {loading ? (
              <div style={styles.loading}>
                <p>Connecting to Instagram...</p>
              </div>
            ) : (
              <>
                <p style={styles.description}>
                  Connect your Instagram account to enable automated campaign publishing.
                  You'll be redirected to Instagram to authorize PostPilot AI.
                </p>

                <div style={styles.features}>
                  <h3 style={styles.featuresTitle}>What we'll do:</h3>
                  <ul style={styles.featuresList}>
                    <li>Publish campaigns to your Instagram feed</li>
                    <li>Fetch analytics and insights</li>
                    <li>Schedule posts for optimal engagement</li>
                  </ul>
                </div>

                <button
                  onClick={handleConnect}
                  style={styles.button}
                  disabled={loading}
                >
                  Connect Instagram Account
                </button>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '80vh',
    padding: '1rem',
  },
  card: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    maxWidth: '500px',
    width: '100%',
  },
  title: {
    fontSize: '2rem',
    color: '#333',
    marginBottom: '1.5rem',
    textAlign: 'center',
  },
  description: {
    color: '#666',
    lineHeight: '1.6',
    marginBottom: '1.5rem',
  },
  features: {
    backgroundColor: '#f8f9fa',
    padding: '1rem',
    borderRadius: '4px',
    marginBottom: '1.5rem',
  },
  featuresTitle: {
    fontSize: '1.1rem',
    color: '#333',
    marginBottom: '0.75rem',
  },
  featuresList: {
    color: '#666',
    lineHeight: '1.8',
    paddingLeft: '1.5rem',
  },
  button: {
    width: '100%',
    padding: '0.75rem',
    backgroundColor: '#E1306C',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
    fontWeight: '500',
  },
  loading: {
    textAlign: 'center',
    padding: '2rem',
    color: '#666',
  },
  error: {
    padding: '1rem',
    backgroundColor: '#fee',
    color: '#c33',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  success: {
    padding: '1rem',
    backgroundColor: '#d4edda',
    color: '#155724',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  connected: {
    textAlign: 'center',
    padding: '2rem 0',
  },
  successIcon: {
    fontSize: '4rem',
    color: '#28a745',
    marginBottom: '1rem',
  },
  connectedTitle: {
    fontSize: '1.5rem',
    color: '#28a745',
    marginBottom: '0.5rem',
  },
  connectedText: {
    color: '#666',
    marginBottom: '1.5rem',
  },
};

export default InstagramConnect;
