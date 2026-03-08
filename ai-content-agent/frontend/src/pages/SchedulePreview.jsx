import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axios from '../api/axios'
import '../styles/SchedulePreview.css'

function SchedulePreview() {
    const navigate = useNavigate()
    const { campaignId } = useParams()
    const [schedule, setSchedule] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [approving, setApproving] = useState(false)
    const [editingPost, setEditingPost] = useState(null)

    useEffect(() => {
        generateSchedule()
    }, [campaignId])

    const generateSchedule = async () => {
        const token = localStorage.getItem('token')
        if (!token) {
            navigate('/login')
            return
        }

        try {
            setLoading(true)
            const response = await axios.post(
                `/campaigns/${campaignId}/schedule`,
                {
                    start_date: new Date().toISOString().split('T')[0],
                    timezone_offset: Math.round(new Date().getTimezoneOffset() / -60)
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            setSchedule(response.data.preview)
        } catch (err) {
            console.error('Schedule generation error:', err.response?.data)
            const errorMessage = err.response?.data?.detail
                ? (typeof err.response.data.detail === 'string'
                    ? err.response.data.detail
                    : JSON.stringify(err.response.data.detail))
                : 'Failed to generate schedule'
            setError(errorMessage)
        } finally {
            setLoading(false)
        }
    }

    const handleApproveSchedule = async () => {
        setApproving(true)

        try {
            // Schedule is already saved in database from the POST request
            // Navigate to analytics page
            navigate(`/campaigns/${campaignId}/analytics`)
        } catch (err) {
            setError('Failed to approve schedule')
        } finally {
            setApproving(false)
        }
    }

    const handleEditTime = (post) => {
        setEditingPost(post)
    }

    const handleSaveTime = async (postId, newTime) => {
        // TODO: Implement time editing API
        console.log('Saving new time:', postId, newTime)
        setEditingPost(null)
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

    if (loading) {
        return (
            <div className="schedule-container">
                <div className="loading">Generating schedule...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="schedule-container">
                <div className="error-state">
                    <h2>Schedule Generation Failed</h2>
                    <p>{error}</p>
                    <button onClick={() => navigate('/dashboard')} className="btn-primary">
                        Back to Dashboard
                    </button>
                </div>
            </div>
        )
    }

    if (!schedule) {
        return null
    }

    const postsByDay = groupPostsByDay(schedule.scheduled_posts)

    return (
        <div className="schedule-container">
            <div className="schedule-header">
                <div>
                    <h1>Schedule Preview</h1>
                    <p>{schedule.campaign_name}</p>
                </div>
                <div className="header-actions">
                    <button
                        onClick={handleApproveSchedule}
                        disabled={approving}
                        className="btn-approve"
                    >
                        {approving ? 'Approving...' : '✓ Approve Schedule'}
                    </button>
                    <button
                        onClick={() => navigate(`/campaigns/${campaignId}/plan`)}
                        className="btn-secondary"
                    >
                        Cancel
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
                <div className="summary-card">
                    <div className="summary-label">Peak Time Posts</div>
                    <div className="summary-value">{schedule.peak_time_percentage}%</div>
                </div>
            </div>

            <div className="platform-distribution">
                <h3>Posts by Platform</h3>
                <div className="platform-chips">
                    {Object.entries(schedule.posts_by_platform).map(([platform, count]) => (
                        <div key={platform} className="platform-chip">
                            <span className="platform-icon">{getPlatformIcon(platform)}</span>
                            <span className="platform-name">{platform}</span>
                            <span className="platform-count">{count}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="schedule-timeline">
                <h3>Posting Schedule</h3>
                {Object.entries(postsByDay).sort(([a], [b]) => a - b).map(([day, posts]) => (
                    <div key={day} className="day-section">
                        <div className="day-header">
                            <h4>Day {day}</h4>
                            <span className="day-date">
                                {posts[0].post_date} ({posts[0].day_of_week})
                            </span>
                            {posts[0].is_weekend && <span className="weekend-badge">Weekend</span>}
                        </div>

                        <div className="posts-list">
                            {posts.map((post, index) => (
                                <PostCard
                                    key={index}
                                    post={post}
                                    onEditTime={handleEditTime}
                                    isEditing={editingPost?.content_id === post.content_id}
                                    onSaveTime={handleSaveTime}
                                    getPlatformIcon={getPlatformIcon}
                                />
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

function PostCard({ post, onEditTime, isEditing, onSaveTime, getPlatformIcon }) {
    const [newTime, setNewTime] = useState(post.post_time)

    return (
        <div className="post-card">
            <div className="post-header">
                <div className="platform-info">
                    <span className="platform-icon-large">{getPlatformIcon(post.platform)}</span>
                    <div>
                        <div className="platform-name-large">{post.platform}</div>
                        <div className="content-type">{post.content_type}</div>
                    </div>
                </div>

                <div className="time-section">
                    {isEditing ? (
                        <div className="time-edit">
                            <input
                                type="time"
                                value={newTime}
                                onChange={(e) => setNewTime(e.target.value)}
                                className="time-input"
                            />
                            <button
                                onClick={() => onSaveTime(post.content_id, newTime)}
                                className="btn-save-time"
                            >
                                Save
                            </button>
                        </div>
                    ) : (
                        <>
                            <div className="scheduled-time">
                                <span className="time-icon">🕐</span>
                                <span className="time-value">{post.post_time}</span>
                                {post.is_peak_time && <span className="peak-badge">Peak Time</span>}
                            </div>
                            <button
                                onClick={() => onEditTime(post)}
                                className="btn-edit-time"
                            >
                                Edit Time
                            </button>
                        </>
                    )}
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
        </div>
    )
}

export default SchedulePreview



