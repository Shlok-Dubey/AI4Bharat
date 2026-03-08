import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import '../styles/Auth.css'

function OAuthSuccess() {
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const provider = searchParams.get('provider')

    useEffect(() => {
        // Redirect to dashboard after 2 seconds
        const timer = setTimeout(() => {
            navigate('/dashboard')
        }, 2000)

        return () => clearTimeout(timer)
    }, [navigate])

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="success-icon">✓</div>
                <h1>Successfully Connected!</h1>
                <p className="auth-subtitle">
                    Your {provider === 'meta' ? 'Instagram' : provider} account has been connected.
                </p>
                <p className="auth-subtitle">
                    Redirecting to dashboard...
                </p>
            </div>
        </div>
    )
}

export default OAuthSuccess


