import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { campaignAPI } from '../services/api';

const CampaignDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [campaign, setCampaign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [scheduling, setScheduling] = useState(false);

  useEffect(() => {
    loadCampaign();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const loadCampaign = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await campaignAPI.get(id);
      setCampaign(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load campaign');
    } finally {
      setLoading(false);
    }
  };

  const handleSchedule = async (e) => {
    e.preventDefault();
    
    if (!scheduledTime) {
      setError('Please select a date and time');
      return;
    }

    setScheduling(true);
    setError('');

    try {
      await campaignAPI.schedule(id, scheduledTime);
      loadCampaign();
      setScheduledTime('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to schedule campaign');
    } finally {
      setScheduling(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this campaign?')) {
      return;
    }

    try {
      await campaignAPI.cancel(id);
      loadCampaign();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to cancel campaign');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      draft: '#6c757d',
      scheduled: '#007bff',
      publishing: '#ffc107',
      published: '#28a745',
      failed: '#dc3545',
      cancelled: '#6c757d',
    };
    return colors[status] || '#6c757d';
  };

  if (loading) {
    return <div style={styles.loading}>Loading campaign...</div>;
  }

  if (!campaign) {
    return <div style={styles.error}>Campaign not found</div>;
  }

  return (
    <div style={styles.container}>
      <button onClick={() => navigate('/campaigns')} style={styles.backButton}>
        ← Back to Campaigns
      </button>

      <div style={styles.card}>
        <div style={styles.header}>
          <h1 style={styles.title}>Campaign Details</h1>
          <span
            style={{
              ...styles.status,
              backgroundColor: getStatusColor(campaign.status),
            }}
          >
            {campaign.status}
          </span>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Caption</h2>
          <p style={styles.caption}>{campaign.caption}</p>
        </div>

        {campaign.hashtags && campaign.hashtags.length > 0 && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Hashtags</h2>
            <div style={styles.hashtags}>
              {campaign.hashtags.map((tag, idx) => (
                <span key={idx} style={styles.hashtag}>
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Information</h2>
          <div style={styles.info}>
            <div style={styles.infoRow}>
              <span style={styles.label}>Campaign ID:</span>
              <span style={styles.value}>{campaign.campaign_id}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.label}>Product ID:</span>
              <span style={styles.value}>{campaign.product_id}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.label}>Created:</span>
              <span style={styles.value}>
                {new Date(campaign.created_at).toLocaleString()}
              </span>
            </div>
            {campaign.scheduled_time && (
              <div style={styles.infoRow}>
                <span style={styles.label}>Scheduled for:</span>
                <span style={styles.value}>
                  {new Date(campaign.scheduled_time).toLocaleString()}
                </span>
              </div>
            )}
            {campaign.published_at && (
              <div style={styles.infoRow}>
                <span style={styles.label}>Published:</span>
                <span style={styles.value}>
                  {new Date(campaign.published_at).toLocaleString()}
                </span>
              </div>
            )}
            {campaign.instagram_post_id && (
              <div style={styles.infoRow}>
                <span style={styles.label}>Instagram Post ID:</span>
                <span style={styles.value}>{campaign.instagram_post_id}</span>
              </div>
            )}
            {campaign.last_error && (
              <div style={styles.infoRow}>
                <span style={styles.label}>Error:</span>
                <span style={{...styles.value, color: '#dc3545'}}>
                  {campaign.last_error}
                </span>
              </div>
            )}
          </div>
        </div>

        {(campaign.status === 'draft' || campaign.status === 'failed') && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Schedule Campaign</h2>
            <form onSubmit={handleSchedule} style={styles.scheduleForm}>
              <input
                type="datetime-local"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                style={styles.dateInput}
                min={new Date().toISOString().slice(0, 16)}
                disabled={scheduling}
              />
              <button
                type="submit"
                style={styles.scheduleButton}
                disabled={scheduling}
              >
                {scheduling ? 'Scheduling...' : 'Schedule'}
              </button>
            </form>
          </div>
        )}

        {campaign.status === 'scheduled' && (
          <div style={styles.actions}>
            <button onClick={handleCancel} style={styles.cancelButton}>
              Cancel Campaign
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '1rem',
  },
  backButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    marginBottom: '1rem',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    padding: '2rem',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
  },
  title: {
    fontSize: '2rem',
    color: '#333',
    margin: 0,
  },
  status: {
    padding: '0.5rem 1rem',
    borderRadius: '12px',
    color: 'white',
    fontSize: '0.9rem',
    fontWeight: '500',
    textTransform: 'uppercase',
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
  section: {
    marginBottom: '2rem',
  },
  sectionTitle: {
    fontSize: '1.25rem',
    color: '#333',
    marginBottom: '1rem',
  },
  caption: {
    color: '#333',
    lineHeight: '1.6',
    fontSize: '1.1rem',
  },
  hashtags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
  },
  hashtag: {
    padding: '0.5rem 1rem',
    backgroundColor: '#e3f2fd',
    color: '#007bff',
    borderRadius: '4px',
    fontSize: '1rem',
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
    minWidth: '150px',
  },
  value: {
    color: '#666',
  },
  scheduleForm: {
    display: 'flex',
    gap: '1rem',
  },
  dateInput: {
    flex: 1,
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  scheduleButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '500',
  },
  actions: {
    display: 'flex',
    gap: '1rem',
  },
  cancelButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '500',
  },
};

export default CampaignDetail;
