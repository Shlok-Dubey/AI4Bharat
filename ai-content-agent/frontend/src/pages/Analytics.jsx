import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from '../api/axios'
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts'
import '../styles/Analytics.css'

function Analytics() {
    const { campaignId } = useParams()
    const navigate = useNavigate()
    const [analytics, setAnalytics] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    useEffect(() => {
        const token = localStorage.getItem('token')
        if (!token) {
            navigate('/login')
            return
        }

        fetchAnalytics(token)
    }, [campaignId, navigate])

    const fetchAnalytics = async (token) => {
        try {
            setLoading(true)
            const response = await axios.get(
                `/campaigns/${campaignId}/analytics`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )
            setAnalytics(response.data)
            setError('')
        } catch (err) {
            console.error('Error fetching analytics:', err)
            const errorMessage = err.response?.data?.detail
                ? (typeof err.response.data.detail === 'string'
                    ? err.response.data.detail
                    : 'Failed to fetch analytics')
                : 'Failed to fetch analytics'
            setError(errorMessage)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="analytics-container">
                <div className="loading">Loading analytics...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="analytics-container">
                <div className="error-message">{error}</div>
                <button onClick={() => navigate('/dashboard')} className="btn-primary">
                    Back to Dashboard
                </button>
            </div>
        )
    }

    if (!analytics) {
        return (
            <div className="analytics-container">
                <div className="error-message">No analytics data available</div>
            </div>
        )
    }

    // Prepare data for charts
    const postPerformanceData = analytics.post_analytics?.map((post, index) => ({
        name: `Post ${index + 1}`,
        views: post.views,
        likes: post.likes,
        comments: post.comments,
        shares: post.shares,
        engagement: post.engagement_rate
    })) || []

    const engagementBreakdown = [
        { name: 'Likes', value: analytics.total_likes, color: '#FF6B6B' },
        { name: 'Comments', value: analytics.total_comments, color: '#4ECDC4' },
        { name: 'Shares', value: analytics.total_shares, color: '#45B7D1' }
    ]

    const overviewStats = [
        {
            label: 'Total Views',
            value: analytics.total_views?.toLocaleString() || '0',
            icon: '👁️'
        },
        {
            label: 'Total Likes',
            value: analytics.total_likes?.toLocaleString() || '0',
            icon: '❤️'
        },
        {
            label: 'Total Comments',
            value: analytics.total_comments?.toLocaleString() || '0',
            icon: '💬'
        },
        {
            label: 'Engagement Rate',
            value: `${analytics.engagement_rate || 0}%`,
            icon: '📊'
        }
    ]

    return (
        <div className="analytics-container">
            <div className="analytics-header">
                <button onClick={() => navigate('/dashboard')} className="btn-back">
                    ← Back
                </button>
                <h1>Campaign Analytics</h1>
                <p className="campaign-id">Campaign ID: {analytics.campaign_id}</p>
            </div>

            <div className="stats-overview">
                {overviewStats.map((stat, index) => (
                    <div key={index} className="stat-card">
                        <div className="stat-icon">{stat.icon}</div>
                        <div className="stat-content">
                            <div className="stat-value">{stat.value}</div>
                            <div className="stat-label">{stat.label}</div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="charts-grid">
                <div className="chart-card">
                    <h3>Post Performance - Views</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={postPerformanceData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="views" fill="#8884d8" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="chart-card">
                    <h3>Engagement Breakdown</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={engagementBreakdown}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {engagementBreakdown.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                <div className="chart-card full-width">
                    <h3>Engagement Metrics by Post</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={postPerformanceData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="likes" stroke="#FF6B6B" strokeWidth={2} />
                            <Line type="monotone" dataKey="comments" stroke="#4ECDC4" strokeWidth={2} />
                            <Line type="monotone" dataKey="shares" stroke="#45B7D1" strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                <div className="chart-card full-width">
                    <h3>Engagement Rate by Post</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={postPerformanceData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="engagement" fill="#95E1D3" name="Engagement Rate (%)" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="posts-table">
                <h3>Detailed Post Analytics</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Post</th>
                            <th>Platform</th>
                            <th>Views</th>
                            <th>Likes</th>
                            <th>Comments</th>
                            <th>Shares</th>
                            <th>Engagement Rate</th>
                        </tr>
                    </thead>
                    <tbody>
                        {analytics.post_analytics?.map((post, index) => (
                            <tr key={post.post_id}>
                                <td>Post {index + 1}</td>
                                <td>
                                    <span className="platform-badge">{post.platform}</span>
                                </td>
                                <td>{post.views?.toLocaleString()}</td>
                                <td>{post.likes?.toLocaleString()}</td>
                                <td>{post.comments?.toLocaleString()}</td>
                                <td>{post.shares?.toLocaleString()}</td>
                                <td>
                                    <span className="engagement-badge">{post.engagement_rate}%</span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="analytics-footer">
                <p className="last-updated">
                    Last updated: {new Date(analytics.fetched_at).toLocaleString()}
                </p>
                <button onClick={() => fetchAnalytics(localStorage.getItem('token'))} className="btn-refresh">
                    🔄 Refresh Data
                </button>
            </div>
        </div>
    )
}

export default Analytics



