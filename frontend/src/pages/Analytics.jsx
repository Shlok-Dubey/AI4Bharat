import { useState, useEffect } from 'react';
import { analyticsAPI } from '../services/api';

const Analytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    // Set default date range (last 30 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    
    setStartDate(start.toISOString().split('T')[0]);
    setEndDate(end.toISOString().split('T')[0]);
  }, []);

  useEffect(() => {
    if (startDate && endDate) {
      loadAnalytics();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await analyticsAPI.getSummary(
        new Date(startDate).toISOString(),
        new Date(endDate).toISOString()
      );
      setAnalytics(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Analytics Dashboard</h1>

      <div style={styles.dateRange}>
        <div style={styles.dateGroup}>
          <label style={styles.label}>Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={styles.dateInput}
          />
        </div>
        <div style={styles.dateGroup}>
          <label style={styles.label}>End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={styles.dateInput}
          />
        </div>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {loading ? (
        <div style={styles.loading}>Loading analytics...</div>
      ) : analytics ? (
        <>
          <div style={styles.statsGrid}>
            <div style={styles.statCard}>
              <div style={styles.statValue}>{analytics.campaign_count}</div>
              <div style={styles.statLabel}>Total Campaigns</div>
            </div>

            <div style={styles.statCard}>
              <div style={styles.statValue}>{formatNumber(analytics.total_likes)}</div>
              <div style={styles.statLabel}>Total Likes</div>
            </div>

            <div style={styles.statCard}>
              <div style={styles.statValue}>{formatNumber(analytics.total_comments)}</div>
              <div style={styles.statLabel}>Total Comments</div>
            </div>

            <div style={styles.statCard}>
              <div style={styles.statValue}>{formatNumber(analytics.total_reach)}</div>
              <div style={styles.statLabel}>Total Reach</div>
            </div>

            <div style={styles.statCard}>
              <div style={styles.statValue}>{formatNumber(analytics.total_impressions)}</div>
              <div style={styles.statLabel}>Total Impressions</div>
            </div>

            <div style={styles.statCard}>
              <div style={styles.statValue}>{analytics.avg_engagement_rate.toFixed(2)}%</div>
              <div style={styles.statLabel}>Avg Engagement Rate</div>
            </div>
          </div>

          {analytics.top_campaigns && analytics.top_campaigns.length > 0 && (
            <div style={styles.section}>
              <h2 style={styles.sectionTitle}>Top Performing Campaigns</h2>
              <div style={styles.table}>
                <div style={styles.tableHeader}>
                  <div style={styles.tableCell}>Campaign</div>
                  <div style={styles.tableCell}>Likes</div>
                  <div style={styles.tableCell}>Comments</div>
                  <div style={styles.tableCell}>Reach</div>
                  <div style={styles.tableCell}>Engagement</div>
                </div>
                {analytics.top_campaigns.map((campaign, idx) => (
                  <div key={idx} style={styles.tableRow}>
                    <div style={styles.tableCell}>
                      {campaign.caption.substring(0, 50)}...
                    </div>
                    <div style={styles.tableCell}>{formatNumber(campaign.likes)}</div>
                    <div style={styles.tableCell}>{formatNumber(campaign.comments)}</div>
                    <div style={styles.tableCell}>{formatNumber(campaign.reach)}</div>
                    <div style={styles.tableCell}>{campaign.engagement_rate.toFixed(2)}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analytics.trends && (
            <div style={styles.section}>
              <h2 style={styles.sectionTitle}>Trends</h2>
              <div style={styles.trendsGrid}>
                <div style={styles.trendCard}>
                  <div style={styles.trendLabel}>Likes Trend</div>
                  <div style={{
                    ...styles.trendValue,
                    color: analytics.trends.likes_trend >= 0 ? '#28a745' : '#dc3545'
                  }}>
                    {analytics.trends.likes_trend >= 0 ? '↑' : '↓'} {Math.abs(analytics.trends.likes_trend).toFixed(1)}%
                  </div>
                </div>

                <div style={styles.trendCard}>
                  <div style={styles.trendLabel}>Comments Trend</div>
                  <div style={{
                    ...styles.trendValue,
                    color: analytics.trends.comments_trend >= 0 ? '#28a745' : '#dc3545'
                  }}>
                    {analytics.trends.comments_trend >= 0 ? '↑' : '↓'} {Math.abs(analytics.trends.comments_trend).toFixed(1)}%
                  </div>
                </div>

                <div style={styles.trendCard}>
                  <div style={styles.trendLabel}>Reach Trend</div>
                  <div style={{
                    ...styles.trendValue,
                    color: analytics.trends.reach_trend >= 0 ? '#28a745' : '#dc3545'
                  }}>
                    {analytics.trends.reach_trend >= 0 ? '↑' : '↓'} {Math.abs(analytics.trends.reach_trend).toFixed(1)}%
                  </div>
                </div>

                <div style={styles.trendCard}>
                  <div style={styles.trendLabel}>Engagement Trend</div>
                  <div style={{
                    ...styles.trendValue,
                    color: analytics.trends.engagement_rate_trend >= 0 ? '#28a745' : '#dc3545'
                  }}>
                    {analytics.trends.engagement_rate_trend >= 0 ? '↑' : '↓'} {Math.abs(analytics.trends.engagement_rate_trend).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        <div style={styles.empty}>
          <p>No analytics data available for the selected date range.</p>
        </div>
      )}
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
  dateRange: {
    display: 'flex',
    gap: '1rem',
    marginBottom: '2rem',
    padding: '1rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  dateGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  label: {
    fontWeight: '500',
    color: '#333',
  },
  dateInput: {
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
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  },
  statCard: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    textAlign: 'center',
  },
  statValue: {
    fontSize: '2rem',
    fontWeight: 'bold',
    color: '#007bff',
    marginBottom: '0.5rem',
  },
  statLabel: {
    color: '#666',
    fontSize: '0.9rem',
  },
  section: {
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    marginBottom: '2rem',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    color: '#333',
    marginBottom: '1rem',
  },
  table: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  tableHeader: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr',
    gap: '1rem',
    padding: '0.75rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
    fontWeight: '600',
    color: '#333',
  },
  tableRow: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr',
    gap: '1rem',
    padding: '0.75rem',
    borderBottom: '1px solid #e0e0e0',
  },
  tableCell: {
    color: '#666',
  },
  trendsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
  },
  trendCard: {
    padding: '1rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
    textAlign: 'center',
  },
  trendLabel: {
    color: '#666',
    fontSize: '0.9rem',
    marginBottom: '0.5rem',
  },
  trendValue: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
  },
};

export default Analytics;
