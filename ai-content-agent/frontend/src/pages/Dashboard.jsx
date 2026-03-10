import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import axios from '../api/axios'
import InstagramConnect from '../components/InstagramConnect'
import '../styles/Dashboard.css'

function Dashboard() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [user, setUser] = useState(null)
  const [oauthAccounts, setOauthAccounts] = useState([])
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')

    if (!token || !userData) {
      navigate('/login')
      return
    }

    setUser(JSON.parse(userData))
    fetchOAuthAccounts(token)
    fetchCampaigns(token)

    const oauthSuccess = searchParams.get('oauth_success')
    if (oauthSuccess === 'true') {
      setSuccessMessage('Instagram Business Account connected successfully!')
      setTimeout(() => setSuccessMessage(''), 5000)
      window.history.replaceState({}, '', '/dashboard')
    }
  }, [navigate, searchParams])

  const fetchOAuthAccounts = async (token) => {
    try {
      const response = await axios.get('/auth/meta/accounts', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      setOauthAccounts(response.data)
    } catch (err) {
      console.error('Error fetching OAuth accounts:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchCampaigns = async (token) => {
    try {
      const response = await axios.get('/campaigns', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      setCampaigns(response.data.campaigns || [])
    } catch (err) {
      console.error('Error fetching campaigns:', err)
    }
  }

  // Calculate statistics from campaigns
  const calculateStats = () => {
    let totalPosts = 0
    let totalScheduled = 0
    let totalPublished = 0

    campaigns.forEach(campaign => {
      totalPosts += campaign.total_content || 0
      totalScheduled += campaign.scheduled_posts || 0
      totalPublished += campaign.published_posts || 0
    })

    return { totalPosts, totalScheduled, totalPublished }
  }

  const stats = calculateStats()

  // Check completion status for getting started checklist
  const hasCreatedCampaign = campaigns.length > 0
  const hasGeneratedContent = campaigns.some(c => (c.total_content || 0) > 0)
  const hasScheduledPost = campaigns.some(c => (c.scheduled_posts || 0) > 0)

  const handleDeleteCampaign = async (campaignId, campaignName) => {
    if (!window.confirm(`Are you sure you want to delete "${campaignName}"? This action cannot be undone.`)) {
      return
    }

    const token = localStorage.getItem('token')
    try {
      await axios.delete(`/campaigns/${campaignId}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      // Refresh campaigns list
      fetchCampaigns(token)
      setSuccessMessage('Campaign deleted successfully!')
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err) {
      console.error('Error deleting campaign:', err)
      alert('Failed to delete campaign. Please try again.')
    }
  }

  const handleConnectionStatusChange = () => {
    const token = localStorage.getItem('token')
    if (token) {
      fetchOAuthAccounts(token)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading...</div>
      </div>
    )
  }

  const isInstagramConnected = oauthAccounts.some(acc => acc.provider === 'meta')

  return (
    <div className="dashboard-container">
      <nav className="dashboard-nav">
        <div className="nav-brand">
          <h2>AI Content Agent</h2>
        </div>
        <div className="nav-actions">
          <span className="user-name">{user?.name}</span>
          <button onClick={handleLogout} className="btn-secondary">
            Logout
          </button>
        </div>
      </nav>

      <div className="dashboard-content">
        <div className="welcome-section">
          <h1>Welcome, {user?.name}!</h1>
          <p>Manage your AI-powered social media campaigns</p>
          {successMessage && (
            <div className="success-banner">
              {successMessage}
            </div>
          )}
          <div className="action-buttons">
            <button
              onClick={() => navigate('/campaigns/create')}
              className="btn-primary btn-large"
              disabled={!isInstagramConnected}
            >
              Create New Campaign
            </button>
            {!isInstagramConnected && (
              <p className="help-text">Connect your Instagram account first to create campaigns</p>
            )}
          </div>
        </div>

        <div className="dashboard-grid">
          <div className="card">
            <h3>Account Information</h3>
            <div className="info-row">
              <span className="label">Email:</span>
              <span className="value">{user?.email}</span>
            </div>
            {user?.business_name && (
              <div className="info-row">
                <span className="label">Business:</span>
                <span className="value">{user.business_name}</span>
              </div>
            )}
            {user?.business_type && (
              <div className="info-row">
                <span className="label">Type:</span>
                <span className="value">{user.business_type}</span>
              </div>
            )}
            <div className="info-row">
              <span className="label">Status:</span>
              <span className={`badge ${user?.is_active ? 'badge-success' : 'badge-error'}`}>
                {user?.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>

          <div className="card">
            <h3>Connected Accounts</h3>
            <div className="connected-accounts">
              <InstagramConnect
                isConnected={isInstagramConnected}
                onStatusChange={handleConnectionStatusChange}
              />
            </div>
            <p className="card-note">
              Connect your Instagram Business Account to start publishing AI-generated content
            </p>
          </div>

          <div className="card">
            <h3>Quick Stats</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{campaigns.length}</div>
                <div className="stat-label">Campaigns</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{stats.totalPosts}</div>
                <div className="stat-label">Content</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{stats.totalScheduled}</div>
                <div className="stat-label">Scheduled</div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3>Getting Started</h3>
            <ul className="checklist">
              <li className="completed">
                <span className="checkmark">✓</span>
                Create your account
              </li>
              <li className={isInstagramConnected ? 'completed' : ''}>
                <span className="checkmark">{isInstagramConnected ? '✓' : '○'}</span>
                Connect Instagram Business Account
              </li>
              <li className={hasCreatedCampaign ? 'completed' : ''}>
                <span className="checkmark">{hasCreatedCampaign ? '✓' : '○'}</span>
                Create your first campaign
              </li>
              <li className={hasGeneratedContent ? 'completed' : ''}>
                <span className="checkmark">{hasGeneratedContent ? '✓' : '○'}</span>
                Generate AI content
              </li>
              <li className={hasScheduledPost ? 'completed' : ''}>
                <span className="checkmark">{hasScheduledPost ? '✓' : '○'}</span>
                Schedule your first post
              </li>
            </ul>
          </div>
        </div>

        {campaigns.length > 0 && (
          <div className="campaigns-section" style={{ marginTop: '32px' }}>
            <h2>Your Campaigns</h2>
            <div className="campaigns-list">
              {campaigns.map((campaign) => (
                <div key={campaign.id} className="campaign-card">
                  <div className="campaign-header">
                    <h3>{campaign.name || campaign.campaign_name}</h3>
                    <span className={`status-badge status-${campaign.status}`}>
                      {campaign.status}
                    </span>
                  </div>
                  <p className="campaign-description">
                    {campaign.campaign_settings?.product_name || 'No product'} - {campaign.campaign_settings?.campaign_days || 0} days
                  </p>
                  <div className="campaign-stats">
                    <div className="campaign-stat">
                      <span className="stat-label">Content:</span>
                      <span className="stat-value">{campaign.total_content || 0}</span>
                    </div>
                    <div className="campaign-stat">
                      <span className="stat-label">Scheduled:</span>
                      <span className="stat-value">{campaign.scheduled_posts || 0}</span>
                    </div>
                    <div className="campaign-stat">
                      <span className="stat-label">Published:</span>
                      <span className="stat-value">{campaign.published_posts || 0}</span>
                    </div>
                  </div>
                  <div className="campaign-actions">
                    <button
                      onClick={() => navigate(`/campaigns/${campaign.id}/review`)}
                      className="btn-primary-small"
                    >
                      Review Content
                    </button>
                    <button
                      onClick={() => navigate(`/campaigns/${campaign.id}/plan`)}
                      className="btn-secondary"
                      style={{ padding: '8px 16px', fontSize: '14px' }}
                    >
                      View Plan
                    </button>
                    {(campaign.scheduled_posts || 0) > 0 && (
                      <button
                        onClick={() => navigate(`/campaigns/${campaign.id}/scheduled-posts`)}
                        className="btn-secondary"
                        style={{ padding: '8px 16px', fontSize: '14px' }}
                      >
                        Scheduled Posts
                      </button>
                    )}
                    <button
                      onClick={() => navigate(`/campaigns/${campaign.id}/analytics`)}
                      className="btn-secondary"
                      style={{ padding: '8px 16px', fontSize: '14px' }}
                    >
                      Analytics
                    </button>
                    <button
                      onClick={() => handleDeleteCampaign(campaign.id, campaign.name || campaign.campaign_name)}
                      className="btn-danger"
                      style={{ padding: '8px 16px', fontSize: '14px', marginLeft: '8px' }}
                      title="Delete campaign"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard



