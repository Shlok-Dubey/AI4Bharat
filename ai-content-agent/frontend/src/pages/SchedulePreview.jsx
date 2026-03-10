import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axios from '../api/axios'
import '../styles/SchedulePreview.css'

function SchedulePreview() {
    console.log('🎯 SchedulePreview component mounted')

    const navigate = useNavigate()
    const { campaignId } = useParams()
    const [schedule, setSchedule] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [approving, setApproving] = useState(false)
    const [editingPost, setEditingPost] = useState(null)

    console.log('📋 Component state - campaignId:', campaignId, 'loading:', loading, 'schedule:', !!schedule, 'error:', error)

    useEffect(() => {
        console.log('🔄 useEffect triggered - campaignId:', campaignId)

        // Reset state when campaignId changes
        setSchedule(null)
        setError('')
        setEditingPost(null)

        // Generate schedule (don't reset loading here, let generateSchedule handle it)
        generateSchedule()
    }, [campaignId]) // Only run when campaignId changes

    const generateSchedule = async () => {
        console.log('🚀 generateSchedule called, campaignId:', campaignId, 'loading:', loading)

        const token = localStorage.getItem('token')
        if (!token) {
            console.log('❌ No token found, redirecting to login')
            navigate('/login')
            return
        }

        // Prevent multiple simultaneous requests
        if (loading) {
            console.log('⏳ Schedule generation already in progress, skipping...')
            return
        }

        // Check if we already have a schedule for this campaign
        if (schedule) {
            console.log('✅ Schedule already exists, skipping generation')
            return
        }

        try {
            console.log('🔄 Setting loading to true and starting request')
            setLoading(true)
            setError('') // Clear any previous errors

            console.log('🚀 Starting schedule generation for campaign:', campaignId)

            const response = await axios.post(
                `/campaigns/${campaignId}/schedule`,
                {
                    start_date: new Date().toISOString().split('T')[0],
                    timezone_offset: Math.round(new Date().getTimezoneOffset() / -60)
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    },
                    timeout: 120000  // 120 seconds for schedule generation (increased from 60)
                }
            )

            console.log('📦 Received response:', response.data)

            // Backend returns ScheduleCreateResponse with preview field
            if (response.data && response.data.preview) {
                setSchedule(response.data.preview)
                console.log('✅ Schedule loaded successfully:', response.data.preview)
            } else {
                console.error('Invalid response structure:', response.data)
                setError('Invalid response from server')
            }
        } catch (err) {
            console.error('Schedule generation error:', err)
            console.error('Error details:', {
                message: err.message,
                response: err.response,
                responseData: err.response?.data,
                status: err.response?.status
            })

            let errorMessage = 'Failed to generate schedule'

            if (err.response?.data?.detail) {
                errorMessage = typeof err.response.data.detail === 'string'
                    ? err.response.data.detail
                    : JSON.stringify(err.response.data.detail)
            } else if (err.message) {
                errorMessage = err.message
            }

            // Special handling for common errors
            if (errorMessage.includes('No approved content found')) {
                errorMessage = 'No approved content found. Please go back and approve some content before scheduling.'
            } else if (errorMessage.includes('Object with ID') && errorMessage.includes('does not exist')) {
                errorMessage = 'Instagram Business Account setup issue. Please ensure your Instagram account is converted to a Business Account and connected to a Facebook Page, then reconnect your account.'
            } else if (errorMessage.includes('Unsupported post request')) {
                errorMessage = 'Instagram publishing not available. Your Instagram account needs to be set up as a Business Account connected to a Facebook Page.'
            }

            setError(errorMessage)
        } finally {
            setLoading(false)
        }
    }

    const handleApproveSchedule = async () => {
        setApproving(true)

        try {
            // Schedule is already saved in database from the POST request
            // Navigate to scheduled posts page to view and manually publish
            navigate(`/campaigns/${campaignId}/scheduled-posts`)
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
        const token = localStorage.getItem('token')
        if (!token) {
            navigate('/login')
            return
        }

        try {
            // Convert time to full datetime
            const currentDate = new Date(editingPost.scheduled_for)
            const [hours, minutes] = newTime.split(':')
            currentDate.setHours(parseInt(hours), parseInt(minutes), 0, 0)

            const newDateTime = currentDate.toISOString().slice(0, 19).replace('T', ' ')

            const response = await axios.patch(
                `/campaigns/${campaignId}/schedule/${postId}/time`,
                {
                    scheduled_for: newDateTime
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            // Update the schedule state with new time
            setSchedule(prevSchedule => ({
                ...prevSchedule,
                scheduled_posts: prevSchedule.scheduled_posts.map(post =>
                    post.post_id === postId
                        ? { ...post, post_time: newTime, scheduled_for: newDateTime }
                        : post
                )
            }))

            setEditingPost(null)
            console.log('Time updated successfully:', response.data)
        } catch (err) {
            console.error('Error updating time:', err)
            let errorMessage = 'Failed to update schedule time'

            if (err.response?.data?.detail) {
                errorMessage = typeof err.response.data.detail === 'string'
                    ? err.response.data.detail
                    : JSON.stringify(err.response.data.detail)
            } else if (err.message) {
                errorMessage = err.message
            }

            setError(errorMessage)
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

    if (loading) {
        return (
            <div className="schedule-container">
                <div className="loading">
                    <div>🤖 Generating AI-optimized schedule...</div>
                    <div style={{ fontSize: '0.9em', marginTop: '10px', opacity: 0.7 }}>
                        This may take up to 60 seconds as we analyze your content and create EventBridge rules
                    </div>
                    <button
                        onClick={() => {
                            console.log('🔄 Manual retry clicked')
                            setLoading(false)
                            setError('')
                            generateSchedule()
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

    if (error) {
        return (
            <div className="schedule-container">
                <div className="error-state">
                    <h2>Schedule Generation Failed</h2>
                    <p>{error}</p>
                    <div style={{ marginTop: '20px' }}>
                        {error.includes('No approved content found') ? (
                            <button
                                onClick={() => navigate(`/campaigns/${campaignId}/plan`)}
                                className="btn-primary"
                            >
                                Go Back to Approve Content
                            </button>
                        ) : (
                            <button
                                onClick={() => {
                                    setError('')
                                    generateSchedule()
                                }}
                                className="btn-primary"
                            >
                                Try Again
                            </button>
                        )}
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

    if (!schedule) {
        return (
            <div className="schedule-container">
                <div className="loading">
                    <div>Ready to generate schedule</div>
                    <div style={{ fontSize: '0.9em', marginTop: '10px', opacity: 0.7 }}>
                        Click the button below to generate your AI-optimized schedule
                    </div>
                    <button
                        onClick={() => {
                            console.log('🔄 Manual generate button clicked')
                            generateSchedule()
                        }}
                        style={{
                            marginTop: '20px',
                            padding: '10px 20px',
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '5px',
                            cursor: 'pointer'
                        }}
                    >
                        🚀 Generate Schedule
                    </button>
                    <button
                        onClick={() => navigate(`/campaigns/${campaignId}/plan`)}
                        style={{
                            marginTop: '10px',
                            marginLeft: '10px',
                            padding: '10px 20px',
                            backgroundColor: '#6c757d',
                            color: 'white',
                            border: 'none',
                            borderRadius: '5px',
                            cursor: 'pointer'
                        }}
                    >
                        Back to Campaign
                    </button>
                </div>
            </div>
        )
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
                                    isEditing={editingPost?.post_id === post.post_id}
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
                                onClick={() => onSaveTime(post.post_id, newTime)}
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



