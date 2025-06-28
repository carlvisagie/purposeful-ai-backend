import { useState, useEffect } from 'react'
import { apiService } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

export default function ClientDashboard() {
  const { user } = useAuth()
  const [sessions, setSessions] = useState([])
  const [crisisAlerts, setCrisisAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [textInput, setTextInput] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [sessionsRes, alertsRes] = await Promise.all([
        apiService.get('/dashboard/coach/sessions?status=completed'),
        apiService.get('/crisis/alerts?status=active')
      ])
      
      setSessions(sessionsRes.data.sessions || [])
      setCrisisAlerts(alertsRes.data.alerts || [])
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCrisisAnalysis = async () => {
    if (!textInput.trim()) return
    
    setAnalyzing(true)
    try {
      const response = await apiService.post('/crisis/analyze', {
        text: textInput
      })
      setAnalysisResult(response.data)
      
      if (response.data.alert_created) {
        fetchDashboardData()
      }
    } catch (error) {
      console.error('Crisis analysis failed:', error)
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading dashboard...</div>
  }

  return (
    <div className="client-dashboard">
      <div className="dashboard-header">
        <h1>Welcome, {user?.first_name}!</h1>
        <p>Your personal coaching dashboard</p>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h2>Crisis Support Check-in</h2>
          <div className="crisis-analysis">
            <textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="How are you feeling today? Share your thoughts..."
              rows={4}
              className="crisis-input"
            />
            <button 
              onClick={handleCrisisAnalysis}
              disabled={analyzing || !textInput.trim()}
              className="btn-primary"
            >
              {analyzing ? 'Analyzing...' : 'Check My Wellbeing'}
            </button>
            
            {analysisResult && (
              <div className={`analysis-result ${analysisResult.crisis_analysis.severity.toLowerCase()}`}>
                <h3>Wellbeing Assessment</h3>
                <p><strong>Risk Level:</strong> {analysisResult.crisis_analysis.severity}</p>
                <p><strong>Score:</strong> {analysisResult.crisis_analysis.score}/10</p>
                
                {analysisResult.crisis_analysis.indicators.length > 0 && (
                  <div>
                    <strong>Areas of Concern:</strong>
                    <ul>
                      {analysisResult.crisis_analysis.indicators.map((indicator, index) => (
                        <li key={index}>{indicator}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {analysisResult.alert_created && (
                  <div className="alert-notice">
                    <strong>Support Alert Created:</strong> Your coach has been notified and will reach out soon.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="dashboard-card">
          <h2>Recent Sessions</h2>
          {sessions.length > 0 ? (
            <div className="sessions-list">
              {sessions.slice(0, 5).map((session) => (
                <div key={session.id} className="session-item">
                  <div className="session-info">
                    <span className="session-type">{session.session_type}</span>
                    <span className="session-date">
                      {new Date(session.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {session.session_rating && (
                    <div className="session-rating">
                      Rating: {session.session_rating}/5
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p>No sessions yet. Your coaching journey will begin here!</p>
          )}
        </div>

        <div className="dashboard-card">
          <h2>Active Support Alerts</h2>
          {crisisAlerts.length > 0 ? (
            <div className="alerts-list">
              {crisisAlerts.map((alert) => (
                <div key={alert.id} className={`alert-item ${alert.severity.toLowerCase()}`}>
                  <div className="alert-info">
                    <span className="alert-severity">{alert.severity}</span>
                    <span className="alert-date">
                      {new Date(alert.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="alert-message">{alert.message}</p>
                  {alert.escalated_to && (
                    <p className="alert-escalation">
                      Support team notified: {alert.escalated_to}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p>No active alerts. You're doing great!</p>
          )}
        </div>

        <div className="dashboard-card">
          <h2>Subscription & Billing</h2>
          <div className="subscription-info">
            <p><strong>Current Plan:</strong> {user?.client_profile?.subscription_tier || 'No active subscription'}</p>
            <button className="btn-secondary">Manage Subscription</button>
            <button className="btn-secondary">View Billing History</button>
          </div>
        </div>
      </div>
    </div>
  )
}
