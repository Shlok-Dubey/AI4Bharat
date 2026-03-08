import { useState, useEffect } from 'react'
import axios from '../api/axios'

function Home() {
    const [apiStatus, setApiStatus] = useState('checking...')

    useEffect(() => {
        axios.get('/health')
            .then(res => setApiStatus(res.data.status))
            .catch(() => setApiStatus('disconnected'))
    }, [])

    return (
        <div style={{ padding: '2rem' }}>
            <h1>AI Content Agent</h1>
            <p>API Status: {apiStatus}</p>
        </div>
    )
}

export default Home



