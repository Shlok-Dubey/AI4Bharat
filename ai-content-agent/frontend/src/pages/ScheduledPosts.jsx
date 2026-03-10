import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axios from '../api/axios'
import '../styles/ScheduledPosts.css'

function ScheduledPosts() {
    console.log('🎯 ScheduledPosts component mounted')

    const navigate = useNavigate()
    const { campaignId } = useParams()
    const [campaign, setCampaign] = useState(null)
    const [schedule, setSchedule] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [publishing, setPublishing] = useState({})

    console.log('📋 ScheduledPosts state - campaignId:', campaignId, 'loading:', loading, 'schedule:', !!schedule, 'error:', error)

    useEffect(() => {
        fetchSchedule()
    }, [campaignId])

    const fetchSchedule = async () => {
        console.log('🚀 fetchSchedule called for campaignId:', campaignId)

        const token = localStorage.getItem('token')
        if (!token) {
            console.log('❌ No token found, redirecting to login')
            navigate('/login')
            return
        }

        try {
            console.log('🔄 Making GET request to /schedule/preview')
            setLoading(true)
            const response = await axios.get(
                `/campaigns/${campaignId}/schedule/preview`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            console.log('📦 Received response:', response.data)
            console.log('✅ Response keys:', Object.keys(response.data))

            setSchedule(response.data)
            setCampaign({ id: campaignId, name: response.data.campaign_name })
            console.log('✅ Schedule and campaign set successfully')
        } catch (err) {
            console.error('❌ Error fetching schedule:', err)
            console.error('Error details:', {
                message: err.message,
                response: err.response,
                responseData: err.response?.data,
                status: err.response?.status
            })

            const errorMessage = err.response?.data?.detail || 'Failed to load scheduled posts'
            setError(errorMessage)
        } finally {
            setLoading(false)
        }
    }

    const handlePublishNow = async (postId, contentId) => {
        const token = localStorage.getItem('token')
        if (!token) {
            navigate('/login')
            return
        }

        if (!window.confirm('Are you sure you want to publish this post to Instagram now?')) {
            return
        }

        setPublishing(prev => ({ ...prev, [postId]: true }))

        try {
            const response = await axios.post(
                `/campaigns/${campaignId}/posts/${postId}/publish`,
                {},
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            alert(`Post published successfully! Instagram Media ID: ${response.data.media_id}`)

            // Refresh the schedule to update status
            fetchSchedule()
        } catch (err) {
            console.error('Error publishing post:', err.response?.data)
            const errorMessage = err.response?.data?.detail || 'Failed to publish post'
            alert(`Publishing failed: ${errorMessage}`)
        } finally {
            setPublishing(prev => ({ ...prev, [postId]: false }))
        }
    }

    const getPlatformIcon = (platform) => {
        const icons = {
            instagram: '📷',
            facebook: '👥',
            twitter: '🐦',
            linkedin: '💼',
            youtube: '📺',
            tiktok: '🎵'
        }
        return icons[platform] || '📱'
    }

    const groupPostsByDay = (posts) => {
        const grouped = {}
        posts.forEach(post => {
            if (!grouped[post.day_number]) {
                grouped[post.day_number] = []
            }
            grouped[post.day_number].push(post)
        })
        return grouped
    }

    const getPostStatus = (post) => {
        // Check if post has been published
        // This would need to be added to the backend response
        return post.status || 'pending'
    }

    if (loading) {
        return (
            <div className="scheduled-posts-container">
                <div className="loading">Loading scheduled posts...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="scheduled-posts-container">
                <div className="error-state">
                    <h2>Failed to Load Schedule</h2>
                    <p>{error}</p>
                    <div style={{ marginTop: '20px' }}>
                        <button
                            onClick={() => {
                                console.log('🔄 Retry button clicked')
                                setError('')
                                fetchSchedule()
                            }}
                            className="btn-primary"
                        >
                            Try Again
                        </button>
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="btn-secondary"
                            style={{ marginLeft: '10px' }}
                        >
                            Back to Dashboard
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    if (!schedule || !schedule.scheduled_posts || schedule.scheduled_posts.length === 0) {
        return (
            <div className="scheduled-posts-container">
                <div className="empty-state">
                    <h2>No Scheduled Posts</h2>
                    <p>This campaign doesn't have any scheduled posts yet.</p>
                    <button onClick={() => navigate(`/campaigns/${campaignId}/plan`)} className="btn-primary">
                        Go to Campaign Plan
                    </button>
                </div>
            </div>
        )
    }

    const postsByDay = groupPostsByDay(schedule.scheduled_posts)

    return (
        <div className="scheduled-posts-container">
            <div className="scheduled-posts-header">
                <div>
                    <h1>Scheduled Posts</h1>
                    <p>{schedule.campaign_name}</p>
                </div>
                <div className="header-actions">
                    <button
                        onClick={() => navigate(`/campaigns/${campaignId}/analytics`)}
                        className="btn-secondary"
                    >
                        View Analytics
                    </button>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="btn-secondary"
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>

            <div className="schedule-summary">
                <div className="summary-card">
                    <div className="summary-label">Total Posts</div>
                    <div className="summary-value">{schedule.total_posts}</div>
                </div>
                <div className="summary-card">
                    <div className="summary-label">Campaign Days</div>
                    <div className="summary-value">{schedule.campaign_days}</div>
                </div>
                <div className="summary-card">
                    <div className="summary-label">Date Range</div>
                    <div className="summary-value">
                        {schedule.start_date} to {schedule.end_date}
                    </div>
                </div>
            </div>

            <div className="posts-timeline">
                <h3>Posts by Day</h3>
                {Object.entries(postsByDay).sort(([a], [b]) => a - b).map(([day, posts]) => (
                    <div key={day} className="day-section">
                        <div className="day-header">
                            <h4>Day {day}</h4>
                            <span className="day-date">
                                {posts[0].post_date} ({posts[0].day_of_week})
                            </span>
                            {posts[0].is_weekend && <span className="weekend-badge">Weekend</span>}
                        </div>

                        <div className="posts-grid">
                            {posts.map((post, index) => (
                                <div key={index} className="scheduled-post-card">
                                    <div className="post-header">
                                        <div className="platform-info">
                                            <span className="platform-icon">{getPlatformIcon(post.platform)}</span>
                                            <div>
                                                <div className="platform-name">{post.platform}</div>
                                                <div className="content-type">{post.content_type}</div>
                                            </div>
                                        </div>
                                        <div className="post-time">
                                            <span className="time-icon">🕐</span>
                                            <span className="time-value">{post.post_time}</span>
                                            {post.is_peak_time && <span className="peak-badge">Peak</span>}
                                        </div>
                                    </div>

                                    <div className="post-content">
                                        <div className="caption-preview">
                                            {post.caption}
                                        </div>
                                        {post.hashtags && (
                                            <div className="hashtags-preview">
                                                {post.hashtags}
                                            </div>
                                        )}
                                    </div>

                                    <div className="post-actions">
                                        <button
                                            onClick={() => handlePublishNow(post.post_id, post.content_id)}
                                            disabled={publishing[post.post_id]}
                                            className="btn-publish"
                                        >
                                            {publishing[post.post_id] ? 'Publishing...' : '🚀 Publish Now'}
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <div className="info-banner">
                <h4>ℹ️ Manual Publishing</h4>
                <p>
                    Automatic posting is currently disabled. Click "Publish Now" on any post to manually publish it to Instagram.
                    Make sure your Instagram Business Account is connected and has valid permissions.
                </p>
            </div>
        </div>
    )
}

export default ScheduledPosts
