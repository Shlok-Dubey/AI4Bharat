import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import '../styles/Auth.css'

function OAuthError() {
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const message = searchParams.get('message') || 'An error occurred during authentication'

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="error-icon">✕</div>
                <h1>Connection Failed</h1>
                <p className="auth-subtitle error-text">
                    {message}
                </p>
                <div className="button-group">
                    <button onClick={() => navigate('/dashboard')} className="btn-primary">
                        Back to Dashboard
                    </button>
                    <Link to="/dashboard" className="btn-secondary">
                        Try Again
                    </Link>
                </div>
            </div>
        </div>
    )
}

export default OAuthError


