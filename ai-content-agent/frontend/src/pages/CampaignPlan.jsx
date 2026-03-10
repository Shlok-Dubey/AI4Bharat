import { useState, useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import axios from '../api/axios'
import '../styles/Dashboard.css'

function CampaignPlan() {
    console.log('🎯 CampaignPlan component mounted')

    const navigate = useNavigate()
    const { campaignId } = useParams()
    const [campaign, setCampaign] = useState(null)
    const [approvedContent, setApprovedContent] = useState([])
    const [loading, setLoading] = useState(true)

    console.log('📋 CampaignPlan state - campaignId:', campaignId, 'loading:', loading, 'campaign:', !!campaign, 'approvedContent:', approvedContent.length)

    useEffect(() => {
        fetchCampaignData()
    }, [campaignId])

    const fetchCampaignData = async () => {
        console.log('🚀 fetchCampaignData called for campaignId:', campaignId)

        const token = localStorage.getItem('token')
        if (!token) {
            console.log('❌ No token found, redirecting to login')
            navigate('/login')
            return
        }

        try {
            console.log('🔄 Fetching campaign details...')
            // Fetch campaign details
            const campaignResponse = await axios.get(
                `/campaigns/${campaignId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )
            console.log('✅ Campaign response:', campaignResponse.data)
            setCampaign(campaignResponse.data)

            console.log('🔄 Fetching approved content...')
            // Fetch approved content
            const contentResponse = await axios.get(
                `/campaigns/${campaignId}/content?status_filter=approved`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )
            console.log('📦 Content response:', contentResponse.data)
            console.log('📋 Content array:', contentResponse.data.content)
            console.log('📊 Content count:', contentResponse.data.content?.length)

            setApprovedContent(contentResponse.data.content)
            console.log('✅ Approved content set successfully')
        } catch (err) {
            console.error('❌ Error fetching campaign data:', err)
            console.error('Error details:', {
                message: err.message,
                response: err.response,
                responseData: err.response?.data,
                status: err.response?.status
            })
        } finally {
            console.log('🏁 Setting loading to false')
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="dashboard-container">
                <div className="loading">
                    <div>Loading campaign...</div>
                    <button
                        onClick={() => {
                            console.log('🔄 Retry button clicked')
                            setLoading(true)
                            fetchCampaignData()
                        }}
                        style={{
                            marginTop: '20px',
                            padding: '10px 20px',
                            backgroundColor: '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '5px',
                            cursor: 'pointer'
                        }}
                    >
                        Retry if stuck
                    </button>
                </div>
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



