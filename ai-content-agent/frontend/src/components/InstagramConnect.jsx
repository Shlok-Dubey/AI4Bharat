import { useState } from 'react'
import axios from '../api/axios'

function InstagramConnect({ isConnected, onStatusChange }) {
    const [connecting, setConnecting] = useState(false)

    const handleConnect = async () => {
        setConnecting(true)
        const token = localStorage.getItem('token')

        if (!token) {
            alert('Please log in first')
            setConnecting(false)
            return
        }

        try {
            // Directly navigate to the OAuth endpoint via ngrok (HTTPS)
            // The backend will redirect to Meta's OAuth page
            window.location.href = `https://studentless-insensitive-renna.ngrok-free.dev/auth/meta/login?token=${token}`
        } catch (error) {
            console.error('Error connecting Instagram:', error)
            alert('Failed to connect Instagram. Please try again.')
            setConnecting(false)
        }
    }

    const handleDisconnect = async () => {
        if (!confirm('Are you sure you want to disconnect your Instagram Business Account?')) {
            return
        }

        const token = localStorage.getItem('token')

        try {
            await axios.delete('/auth/meta/disconnect/meta', {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            })

            if (onStatusChange) {
                onStatusChange(false)
            }
        } catch (error) {
            console.error('Error disconnecting Instagram:', error)
            alert('Failed to disconnect Instagram account')
        }
    }

    return (
        <div className="instagram-connect">
            {isConnected ? (
                <div className="account-item connected">
                    <div className="account-info">
                        <svg className="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
                        </svg>
                        <div>
                            <div className="account-name">Instagram Business Account</div>
                            <div className="account-status status-connected">Connected</div>
                        </div>
                    </div>
                    <button onClick={handleDisconnect} className="btn-danger-small">
                        Disconnect
                    </button>
                </div>
            ) : (
                <div className="account-item">
                    <div className="account-info">
                        <svg className="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
                        </svg>
                        <div>
                            <div className="account-name">Instagram Business Account</div>
                            <div className="account-status status-not-connected">Not Connected</div>
                        </div>
                    </div>
                    <button
                        onClick={handleConnect}
                        className="btn-primary-small"
                        disabled={connecting}
                    >
                        {connecting ? 'Connecting...' : 'Connect Instagram Business Account'}
                    </button>
                </div>
            )}
        </div>
    )
}

export default InstagramConnect



