import { useState, useEffect } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import axios from '../api/axios'
import '../styles/ReviewContent.css'

function ReviewContent() {
    const navigate = useNavigate()
    const { campaignId } = useParams()
    const [searchParams] = useSearchParams()
    const [content, setContent] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [processingIds, setProcessingIds] = useState(new Set())

    useEffect(() => {
        fetchContent()
    }, [campaignId])

    const fetchContent = async () => {
        const token = localStorage.getItem('token')
        if (!token) {
            navigate('/login')
            return
        }

        try {
            setLoading(true)
            const response = await axios.get(
                `/campaigns/${campaignId}/content?status_filter=pending`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            setContent(response.data.content)
        } catch (err) {
            const errorMessage = err.response?.data?.detail
                ? (typeof err.response.data.detail === 'string'
                    ? err.response.data.detail
                    : 'Failed to load content')
                : 'Failed to load content'
            setError(errorMessage)
        } finally {
            setLoading(false)
        }
    }

    const handleApprove = async (contentId) => {
        const token = localStorage.getItem('token')
        setProcessingIds(prev => new Set(prev).add(contentId))

        try {
            await axios.put(
                `/content/${contentId}/approve`,
                { approved: true },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            // Remove from list
            setContent(prev => prev.filter(c => c.id !== contentId))

            // If no more content, redirect to campaign planning
            if (content.length === 1) {
                navigate(`/campaigns/${campaignId}/plan`)
            }
        } catch (err) {
            const errorMessage = err.response?.data?.detail
                ? (typeof err.response.data.detail === 'string'
                    ? err.response.data.detail
                    : 'Failed to approve content')
                : 'Failed to approve content'
            setError(errorMessage)
        } finally {
            setProcessingIds(prev => {
                const newSet = new Set(prev)
                newSet.delete(contentId)
                return newSet
            })
        }
    }

    const handleRegenerate = async (contentId) => {
        const token = localStorage.getItem('token')
        setProcessingIds(prev => new Set(prev).add(contentId))

        try {
            // Get the content details
            const contentItem = content.find(c => c.id === contentId)

            // Reject the current content
            await axios.put(
                `/content/${contentId}/approve`,
                {
                    approved: false,
                    feedback: 'User requested regeneration'
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            // Generate new content
            await axios.post(
                `/campaigns/${campaignId}/generate-content`,
                {
                    platform: contentItem.platform,
                    content_type: contentItem.content_type,
                    count: 1
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            // Refresh content list
            await fetchContent()
        } catch (err) {
            const errorMessage = err.response?.data?.detail
                ? (typeof err.response.data.detail === 'string'
                    ? err.response.data.detail
                    : 'Failed to regenerate content')
                : 'Failed to regenerate content'
            setError(errorMessage)
        } finally {
            setProcessingIds(prev => {
                const newSet = new Set(prev)
                newSet.delete(contentId)
                return newSet
            })
        }
    }

    const handleApproveAll = async () => {
        const token = localStorage.getItem('token')

        try {
            // Approve all content pieces
            await Promise.all(
                content.map(item =>
                    axios.put(
                        `/content/${item.id}/approve`,
                        { approved: true },
                        {
                            headers: {
                                Authorization: `Bearer ${token}`
                            }
                        }
                    )
                )
            )

            // Redirect to campaign planning
            navigate(`/campaigns/${campaignId}/plan`)
        } catch (err) {
            setError('Failed to approve all content')
        }
    }

    const getPlatformIcon = (platform) => {
        const icons = {
            instagram: '📷',
            facebook: '👥',
            twitter: '🐦',
            linkedin: '💼'
        }
        return icons[platform] || '📱'
    }

    const getContentTypeLabel = (type) => {
        const labels = {
            post: 'Post',
            story: 'Story',
            reel: 'Reel',
            tweet: 'Tweet'
        }
        return labels[type] || type
    }

    if (loading) {
        return (
            <div className="review-container">
                <div className="loading">Loading content...</div>
            </div>
        )
    }

    if (content.length === 0) {
        return (
            <div className="review-container">
                <div className="empty-state">
                    <h2>No Content to Review</h2>
                    <p>All content has been reviewed or no content has been generated yet.</p>
                    <button onClick={() => navigate('/dashboard')} className="btn-primary">
                        Back to Dashboard
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="review-container">
            <div className="review-header">
                <div>
                    <h1>Review Generated Content</h1>
                    <p>Review and approve AI-generated content for your campaign</p>
                </div>
                <div className="header-actions">
                    <button onClick={handleApproveAll} className="btn-success">
                        Approve All ({content.length})
                    </button>
                    <button onClick={() => navigate('/dashboard')} className="btn-secondary">
                        Back to Dashboard
                    </button>
                </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="content-grid">
                {content.map((item) => (
                    <ContentCard
                        key={item.id}
                        content={item}
                        onApprove={handleApprove}
                        onRegenerate={handleRegenerate}
                        isProcessing={processingIds.has(item.id)}
                        getPlatformIcon={getPlatformIcon}
                        getContentTypeLabel={getContentTypeLabel}
                    />
                ))}
            </div>
        </div>
    )
}

function ContentCard({
    content,
    onApprove,
    onRegenerate,
    isProcessing,
    getPlatformIcon,
    getContentTypeLabel
}) {
    const [showFullCaption, setShowFullCaption] = useState(false)
    const [showScript, setShowScript] = useState(false)

    const metadata = content.ai_metadata || {}
    const reelScript = metadata.reel_script
    const thumbnailText = metadata.thumbnail_text

    return (
        <div className="content-card">
            <div className="content-header">
                <div className="platform-badge">
                    <span className="platform-icon">{getPlatformIcon(content.platform)}</span>
                    <span className="platform-name">{content.platform}</span>
                </div>
                <div className="content-type-badge">
                    {getContentTypeLabel(content.content_type)}
                </div>
            </div>

            <div className="content-body">
                <div className="content-section">
                    <h3>Caption</h3>
                    <div className={`caption-text ${showFullCaption ? 'expanded' : ''}`}>
                        {content.caption}
                    </div>
                    {content.caption.length > 200 && (
                        <button
                            onClick={() => setShowFullCaption(!showFullCaption)}
                            className="btn-link"
                        >
                            {showFullCaption ? 'Show less' : 'Show more'}
                        </button>
                    )}
                </div>

                {content.hashtags && (
                    <div className="content-section">
                        <h3>Hashtags</h3>
                        <div className="hashtags">
                            {content.hashtags}
                        </div>
                    </div>
                )}

                {reelScript && (
                    <div className="content-section">
                        <h3>Reel Script</h3>
                        {showScript ? (
                            <div className="script-text">
                                <pre>{reelScript}</pre>
                                <button
                                    onClick={() => setShowScript(false)}
                                    className="btn-link"
                                >
                                    Hide script
                                </button>
                            </div>
                        ) : (
                            <button
                                onClick={() => setShowScript(true)}
                                className="btn-link"
                            >
                                View script
                            </button>
                        )}
                    </div>
                )}

                {thumbnailText && (
                    <div className="content-section">
                        <h3>Thumbnail Text</h3>
                        <div className="thumbnail-preview">
                            {thumbnailText}
                        </div>
                    </div>
                )}
            </div>

            <div className="content-actions">
                <button
                    onClick={() => onApprove(content.id)}
                    disabled={isProcessing}
                    className="btn-approve"
                >
                    {isProcessing ? 'Processing...' : '✓ Approve'}
                </button>
                <button
                    onClick={() => onRegenerate(content.id)}
                    disabled={isProcessing}
                    className="btn-regenerate"
                >
                    {isProcessing ? 'Processing...' : '↻ Regenerate'}
                </button>
            </div>
        </div>
    )
}

export default ReviewContent



