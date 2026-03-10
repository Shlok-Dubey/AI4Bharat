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

        // Generate demo analytics data
        generateDemoAnalytics()
    }, [campaignId, navigate])

    const generateDemoAnalytics = () => {
        setLoading(true)

        // Simulate API delay
        setTimeout(() => {
            // Generate random demo data
            const demoData = {
                campaign_id: campaignId,
                campaign_name: "Demo Campaign",
                total_posts: 8,
                total_views: Math.floor(Math.random() * 50000) + 10000,
                total_likes: Math.floor(Math.random() * 5000) + 1000,
                total_comments: Math.floor(Math.random() * 500) + 100,
                total_shares: Math.floor(Math.random() * 300) + 50,
                engagement_rate: (Math.random() * 5 + 2).toFixed(1), // 2-7%
                fetched_at: new Date().toISOString(),
                post_analytics: []
            }

            // Generate individual post analytics
            const platforms = ['instagram', 'facebook', 'twitter', 'linkedin']
            const postTypes = ['image', 'video', 'carousel', 'story']

            for (let i = 0; i < 8; i++) {
                const views = Math.floor(Math.random() * 8000) + 1000
                const likes = Math.floor(views * (Math.random() * 0.1 + 0.02)) // 2-12% of views
                const comments = Math.floor(likes * (Math.random() * 0.15 + 0.05)) // 5-20% of likes
                const shares = Math.floor(likes * (Math.random() * 0.1 + 0.02)) // 2-12% of likes
                const engagementRate = (((likes + comments + shares) / views) * 100).toFixed(1)

                demoData.post_analytics.push({
                    post_id: `demo-post-${i + 1}`,
                    platform: platforms[Math.floor(Math.random() * platforms.length)],
                    content_type: postTypes[Math.floor(Math.random() * postTypes.length)],
                    views: views,
                    likes: likes,
                    comments: comments,
                    shares: shares,
                    engagement_rate: parseFloat(engagementRate),
                    published_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(), // Random date in last 7 days
                    caption: `Demo post ${i + 1} - Sample content for analytics demonstration`
                })
            }

            // Calculate totals from individual posts
            demoData.total_views = demoData.post_analytics.reduce((sum, post) => sum + post.views, 0)
            demoData.total_likes = demoData.post_analytics.reduce((sum, post) => sum + post.likes, 0)
            demoData.total_comments = demoData.post_analytics.reduce((sum, post) => sum + post.comments, 0)
            demoData.total_shares = demoData.post_analytics.reduce((sum, post) => sum + post.shares, 0)

            const totalEngagements = demoData.total_likes + demoData.total_comments + demoData.total_shares
            demoData.engagement_rate = ((totalEngagements / demoData.total_views) * 100).toFixed(1)

            setAnalytics(demoData)
            setError('')
            setLoading(false)
        }, 1000) // 1 second delay to simulate loading
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
            <div className="demo-banner">
                <div className="demo-notice">
                    📊 <strong>Demo Analytics</strong> - This is sample data for demonstration purposes.
                    Real analytics will be available once Instagram Business Account is properly configured.
                </div>
            </div>

            <div className="analytics-header">
                <button onClick={() => navigate('/dashboard')} className="btn-back">
                    ← Back
                </button>
                <h1>Campaign Analytics</h1>
                <p className="campaign-id">Campaign: {analytics.campaign_name}</p>
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
                    Demo data generated: {new Date(analytics.fetched_at).toLocaleString()}
                </p>
                <button onClick={() => generateDemoAnalytics()} className="btn-refresh">
                    🎲 Generate New Demo Data
                </button>
            </div>
        </div>
    )
}

export default Analytics



