import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from '../api/axios'
import FileUpload from '../components/FileUpload'
import '../styles/Auth.css'
import '../styles/FileUpload.css'

function CreateCampaign() {
    const navigate = useNavigate()
    const [formData, setFormData] = useState({
        campaign_name: '',
        product_name: '',
        product_description: '',
        campaign_days: 30
    })
    const [selectedFiles, setSelectedFiles] = useState([])
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        })
    }

    const handleFilesSelected = (files) => {
        setSelectedFiles(files)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        const token = localStorage.getItem('token')
        if (!token) {
            navigate('/login')
            return
        }

        try {
            // Step 1: Create campaign
            const campaignResponse = await axios.post(
                '/campaigns',
                formData,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            const campaignId = campaignResponse.data.id

            // Step 2: Upload assets if any
            if (selectedFiles.length > 0) {
                const formDataFiles = new FormData()
                selectedFiles.forEach(file => {
                    formDataFiles.append('files', file)
                })

                await axios.post(
                    `/campaigns/${campaignId}/upload-assets`,
                    formDataFiles,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                            'Content-Type': 'multipart/form-data'
                        }
                    }
                )
            }

            // Step 3: Trigger content generation for Instagram
            await axios.post(
                `/campaigns/${campaignId}/generate-content`,
                {
                    platform: "instagram",
                    content_type: "post",
                    count: 5
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            // Redirect to review content page
            navigate(`/campaigns/${campaignId}/review`)
        } catch (err) {
            const errorMessage = err.response?.data?.detail
                ? (typeof err.response.data.detail === 'string'
                    ? err.response.data.detail
                    : JSON.stringify(err.response.data.detail))
                : 'Failed to create campaign. Please try again.'
            setError(errorMessage)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-container">
            <div className="auth-card" style={{ maxWidth: '600px' }}>
                <h1>Create Campaign</h1>
                <p className="auth-subtitle">Set up your AI-powered social media campaign</p>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label htmlFor="campaign_name">Campaign Name</label>
                        <input
                            type="text"
                            id="campaign_name"
                            name="campaign_name"
                            value={formData.campaign_name}
                            onChange={handleChange}
                            required
                            minLength={2}
                            placeholder="Summer Product Launch"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="product_name">Product Name</label>
                        <input
                            type="text"
                            id="product_name"
                            name="product_name"
                            value={formData.product_name}
                            onChange={handleChange}
                            required
                            minLength={2}
                            placeholder="EcoBottle Pro"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="product_description">Product Description</label>
                        <textarea
                            id="product_description"
                            name="product_description"
                            value={formData.product_description}
                            onChange={handleChange}
                            required
                            minLength={10}
                            rows={4}
                            placeholder="Describe your product in detail. This will help AI generate better content."
                            style={{
                                padding: '12px 16px',
                                border: '1px solid #e2e8f0',
                                borderRadius: '8px',
                                fontSize: '14px',
                                fontFamily: 'inherit',
                                resize: 'vertical'
                            }}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="campaign_days">Campaign Duration (Days)</label>
                        <input
                            type="number"
                            id="campaign_days"
                            name="campaign_days"
                            value={formData.campaign_days}
                            onChange={handleChange}
                            required
                            min={1}
                            max={365}
                        />
                    </div>

                    <div className="form-group">
                        <label>Product Images/Videos (Optional)</label>
                        <FileUpload onFilesSelected={handleFilesSelected} maxFiles={5} />
                    </div>

                    <button type="submit" className="btn-primary" disabled={loading}>
                        {loading ? 'Creating Campaign...' : 'Create Campaign'}
                    </button>
                </form>

                <p className="auth-footer">
                    <a href="/dashboard" style={{ color: '#667eea', textDecoration: 'none' }}>
                        ← Back to Dashboard
                    </a>
                </p>
            </div>
        </div>
    )
}

export default CreateCampaign



