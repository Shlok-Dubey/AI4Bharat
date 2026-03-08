import { useState, useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import axios from '../api/axios'
import '../styles/Dashboard.css'

function CampaignPlan() {
    const navigate = useNavigate()
    const { campaignId } = useParams()
    const [campaign, setCampaign] = useState(null)
    const [approvedContent, setApprovedContent] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchCampaignData()
    }, [campaignId])

    const fetchCampaignData = async () => {
        const token = localStorage.getItem('token')
        if (!token) {
            navigate('/login')
            return
        }

        try {
            // Fetch campaign details
            const campaignResponse = await axios.get(
                `/campaigns/${campaignId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )
            setCampaign(campaignResponse.data)

            // Fetch approved content
            const contentResponse = await axios.get(
                `/campaigns/${campaignId}/content?status_filter=approved`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )
            setApprovedContent(contentResponse.data.content)
        } catch (err) {
            console.error('Error fetching campaign data:', err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="dashboard-container">
                <div className="loading">Loading campaign...</div>
            </div>
        )
    }

    return (
        <div className="dashboard-container">
            <div className="dashboard-content">
                <div className="welcome-section">
                    <h1>Campaign Planning</h1>
                    <p>{campaign?.campaign_name}</p>
                </div>

                <div className="dashboard-grid">
                    <div className="card">
                        <h3>Approved Content</h3>
                        <div className="stat-value">{approvedContent.length}</div>
                        <p>Content pieces ready for scheduling</p>
                    </div>

                    <div className="card">
                        <h3>Next Steps</h3>
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                            <li style={{ padding: '8px 0' }}>✓ Content generated and approved</li>
                            <li style={{ padding: '8px 0' }}>→ Schedule posts</li>
                            <li style={{ padding: '8px 0' }}>→ Publish to social media</li>
                            <li style={{ padding: '8px 0' }}>→ Track analytics</li>
                        </ul>
                        <button
                            onClick={() => navigate(`/campaigns/${campaignId}/schedule`)}
                            className="btn-primary"
                            style={{ marginTop: '16px', width: '100%' }}
                            disabled={approvedContent.length === 0}
                        >
                            Schedule Posts
                        </button>
                    </div>
                </div>

                <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="btn-secondary"
                    >
                        Back to Dashboard
                    </button>
                    <button
                        onClick={() => navigate(`/campaigns/${campaignId}/analytics`)}
                        className="btn-secondary"
                    >
                        View Analytics
                    </button>
                </div>
            </div>
        </div>
    )
}

export default CampaignPlan



