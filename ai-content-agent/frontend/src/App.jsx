import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Signup from './pages/Signup'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import CreateCampaign from './pages/CreateCampaign'
import ReviewContent from './pages/ReviewContent'
import CampaignPlan from './pages/CampaignPlan'
import SchedulePreview from './pages/SchedulePreview'
import Analytics from './pages/Analytics'
import OAuthSuccess from './pages/OAuthSuccess'
import OAuthError from './pages/OAuthError'

function App() {
    return (
        <Router future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
            <Routes>
                <Route path="/" element={<Navigate to="/login" replace />} />
                <Route path="/signup" element={<Signup />} />
                <Route path="/login" element={<Login />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/campaigns/create" element={<CreateCampaign />} />
                <Route path="/campaigns/:campaignId/review" element={<ReviewContent />} />
                <Route path="/campaigns/:campaignId/plan" element={<CampaignPlan />} />
                <Route path="/campaigns/:campaignId/schedule" element={<SchedulePreview />} />
                <Route path="/campaigns/:campaignId/analytics" element={<Analytics />} />
                <Route path="/oauth/success" element={<OAuthSuccess />} />
                <Route path="/oauth/error" element={<OAuthError />} />
            </Routes>
        </Router>
    )
}

export default App


