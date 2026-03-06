import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { campaignAPI } from '../services/api';

const Campaigns = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    loadCampaigns();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter]);

  const loadCampaigns = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await campaignAPI.list(page, 20, statusFilter || null);
      setCampaigns(response.data.campaigns);
      setHasMore(response.data.has_more);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (campaignId) => {
    if (!confirm('Are you sure you want to cancel this campaign?')) {
      return;
    }

    try {
      await campaignAPI.cancel(campaignId);
      loadCampaigns();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to cancel campaign');
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
    return <div style={styles.loading}>Loading campaigns...</div>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Campaigns</h1>
      </div>

      <div style={styles.filters}>
        <label style={styles.filterLabel}>Filter by status:</label>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          style={styles.select}
        >
          <option value="">All</option>
          <option value="draft">Draft</option>
          <option value="scheduled">Scheduled</option>
          <option value="published">Published</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {campaigns.length === 0 ? (
        <div style={styles.empty}>
          <p>No campaigns found.</p>
        </div>
      ) : (
        <>
          <div style={styles.list}>
            {campaigns.map((campaign) => (
              <div key={campaign.campaign_id} style={styles.card}>
                <div style={styles.cardHeader}>
                  <span
                    style={{
                      ...styles.status,
                      backgroundColor: getStatusColor(campaign.status),
                    }}
                  >
                    {campaign.status}
                  </span>
                  <span style={styles.date}>
                    {new Date(campaign.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div style={styles.cardContent}>
                  <p style={styles.caption}>{campaign.caption}</p>
                  
                  {campaign.hashtags && campaign.hashtags.length > 0 && (
                    <div style={styles.hashtags}>
                      {campaign.hashtags.map((tag, idx) => (
                        <span key={idx} style={styles.hashtag}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {campaign.scheduled_time && (
                    <p style={styles.scheduledTime}>
                      Scheduled for: {new Date(campaign.scheduled_time).toLocaleString()}
                    </p>
                  )}

                  {campaign.published_at && (
                    <p style={styles.publishedAt}>
                      Published: {new Date(campaign.published_at).toLocaleString()}
                    </p>
                  )}

                  {campaign.last_error && (
                    <p style={styles.errorText}>Error: {campaign.last_error}</p>
                  )}
                </div>

                <div style={styles.actions}>
                  <Link
                    to={`/campaigns/${campaign.campaign_id}`}
                    style={styles.viewButton}
                  >
                    View Details
                  </Link>
                  
                  {campaign.status === 'scheduled' && (
                    <button
                      onClick={() => handleCancel(campaign.campaign_id)}
                      style={styles.cancelButton}
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div style={styles.pagination}>
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              style={styles.pageButton}
            >
              Previous
            </button>
            <span style={styles.pageInfo}>Page {page}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={!hasMore}
              style={styles.pageButton}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
};

const styles = {
  container: {
    padding: '1rem',
  },
  header: {
    marginBottom: '2rem',
  },
  title: {
    fontSize: '2rem',
    color: '#333',
  },
  filters: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    marginBottom: '2rem',
    padding: '1rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  filterLabel: {
    fontWeight: '500',
    color: '#333',
  },
  select: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
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
  empty: {
    textAlign: 'center',
    padding: '3rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    marginBottom: '2rem',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    padding: '1.5rem',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  status: {
    padding: '0.25rem 0.75rem',
    borderRadius: '12px',
    color: 'white',
    fontSize: '0.85rem',
    fontWeight: '500',
    textTransform: 'uppercase',
  },
  date: {
    color: '#666',
    fontSize: '0.9rem',
  },
  cardContent: {
    marginBottom: '1rem',
  },
  caption: {
    color: '#333',
    lineHeight: '1.6',
    marginBottom: '1rem',
  },
  hashtags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
    marginBottom: '1rem',
  },
  hashtag: {
    padding: '0.25rem 0.5rem',
    backgroundColor: '#e3f2fd',
    color: '#007bff',
    borderRadius: '4px',
    fontSize: '0.85rem',
  },
  scheduledTime: {
    color: '#666',
    fontSize: '0.9rem',
    marginBottom: '0.5rem',
  },
  publishedAt: {
    color: '#28a745',
    fontSize: '0.9rem',
    marginBottom: '0.5rem',
  },
  errorText: {
    color: '#dc3545',
    fontSize: '0.9rem',
  },
  actions: {
    display: 'flex',
    gap: '0.5rem',
  },
  viewButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '4px',
    fontSize: '0.9rem',
  },
  cancelButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '1rem',
  },
  pageButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  pageInfo: {
    color: '#666',
  },
};

export default Campaigns;
