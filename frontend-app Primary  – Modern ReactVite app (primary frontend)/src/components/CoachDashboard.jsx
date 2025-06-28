import { useState, useEffect } from 'react'
import { apiService } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

export default function CoachDashboard() {
  const { user } = useAuth()
  const [overview, setOverview] = useState(null)
  const [clients, setClients] = useState([])
  const [sessions, setSessions] = useState([])
  const [crisisAlerts, setCrisisAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [overviewRes, clientsRes, sessionsRes, alertsRes] = await Promise.all([
        apiService.get('/dashboard/coach/overview'),
        apiService.get('/dashboard/coach/clients'),
        apiService.get('/dashboard/coach/sessions'),
        apiService.get('/crisis/alerts?status=active')
      ])
      
      setOverview(overviewRes.data.overview)
      setClients(clientsRes.data.clients)
      setSessions(sessionsRes.data.sessions)
      setCrisisAlerts(alertsRes.data.alerts)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleResolveAlert = async (alertId, resolutionNotes) => {
    try {
      await apiService.post(`/crisis/alerts/${alertId}/resolve`, {
        resolution_notes: resolutionNotes
      })
      fetchDashboardData()
    } catch (error) {
      console.error('Failed to resolve alert:', error)
    }
  }

  if (loading) {
    return <div className="loading">Loading coach dashboard...</div>
  }

  return (
    <div className="coach-dashboard">
      <div className="dashboard-header">
        <h1>Coach Dashboard</h1>
        <p>Welcome back, {user?.first_name}!</p>
      </div>

      <div className="dashboard-tabs">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={activeTab === 'clients' ? 'active' : ''}
          onClick={() => setActiveTab('clients')}
        >
          Clients ({clients.length})
        </button>
        <button 
          className={activeTab === 'sessions' ? 'active' : ''}
          onClick={() => setActiveTab('sessions')}
        >
          Sessions
        </button>
        <button 
          className={activeTab === 'alerts' ? 'active' : ''}
          onClick={() => setActiveTab('alerts')}
        >
          Crisis Alerts ({crisisAlerts.length})
        </button>
      </div>

      <div className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="overview-grid">
            <div className="stat-card">
              <h3>Total Clients</h3>
              <div className="stat-number">{overview?.total_clients || 0}</div>
            </div>
            
            <div className="stat-card">
              <h3>Active Sessions</h3>
              <div className="stat-number">{overview?.active_sessions || 0}</div>
            </div>
            
            <div className="stat-card">
              <h3>Sessions Today</h3>
              <div className="stat-number">{overview?.sessions_today || 0}</div>
            </div>
            
            <div className="stat-card alert">
              <h3>Crisis Alerts</h3>
              <div className="stat-number">{overview?.active_crisis_alerts || 0}</div>
            </div>

            <div className="dashboard-card full-width">
              <h2>Risk Distribution</h2>
              <div className="risk-chart">
                {overview?.risk_distribution && Object.entries(overview.risk_distribution).map(([level, count]) => (
                  <div key={level} className="risk-item">
                    <span className={`risk-level level-${level}`}>Risk Level {level}</span>
                    <span className="risk-count">{count} clients</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'clients' && (
          <div className="clients-section">
            <div className="clients-grid">
              {clients.map((client) => (
                <div key={client.id} className="client-card">
                  <div className="client-header">
                    <h3>{client.user_info.first_name} {client.user_info.last_name}</h3>
                    <span className={`risk-badge level-${client.risk_level}`}>
                      Risk: {client.risk_level}
                    </span>
                  </div>
                  
                  <div className="client-info">
                    <p><strong>Email:</strong> {client.user_info.email}</p>
                    <p><strong>Phone:</strong> {client.user_info.phone || 'Not provided'}</p>
                    <p><strong>Subscription:</strong> {client.subscription_tier || 'None'}</p>
                    
                    {client.last_session && (
                      <p><strong>Last Session:</strong> {new Date(client.last_session.created_at).toLocaleDateString()}</p>
                    )}
                    
                    {client.active_crisis_alerts > 0 && (
                      <div className="alert-badge">
                        {client.active_crisis_alerts} Active Alert(s)
                      </div>
                    )}
                  </div>
                  
                  <div className="client-actions">
                    <button className="btn-primary">View Details</button>
                    <button className="btn-secondary">Schedule Session</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'sessions' && (
          <div className="sessions-section">
            <div className="sessions-list">
              {sessions.map((session) => (
                <div key={session.id} className="session-card">
                  <div className="session-header">
                    <h3>{session.client_name}</h3>
                    <span className="session-type">{session.session_type}</span>
                  </div>
                  
                  <div className="session-details">
                    <p><strong>Date:</strong> {new Date(session.created_at).toLocaleString()}</p>
                    {session.duration_minutes && (
                      <p><strong>Duration:</strong> {session.duration_minutes} minutes</p>
                    )}
                    {session.session_rating && (
                      <p><strong>Rating:</strong> {session.session_rating}/5</p>
                    )}
                    {session.risk_level > 1 && (
                      <p><strong>Risk Level:</strong> {session.risk_level}</p>
                    )}
                  </div>
                  
                  {session.notes && (
                    <div className="session-notes">
                      <strong>Notes:</strong>
                      <p>{session.notes}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="alerts-section">
            <div className="alerts-list">
              {crisisAlerts.map((alert) => (
                <CrisisAlertCard 
                  key={alert.id} 
                  alert={alert} 
                  onResolve={handleResolveAlert}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function CrisisAlertCard({ alert, onResolve }) {
  const [resolving, setResolving] = useState(false)
  const [resolutionNotes, setResolutionNotes] = useState('')
  const [showResolveForm, setShowResolveForm] = useState(false)

  const handleResolve = async () => {
    setResolving(true)
    await onResolve(alert.id, resolutionNotes)
    setResolving(false)
    setShowResolveForm(false)
    setResolutionNotes('')
  }

  return (
    <div className={`alert-card severity-${alert.severity.toLowerCase()}`}>
      <div className="alert-header">
        <h3>{alert.client_name}</h3>
        <span className="severity-badge">{alert.severity}</span>
      </div>
      
      <div className="alert-details">
        <p><strong>Created:</strong> {new Date(alert.created_at).toLocaleString()}</p>
        <p><strong>Message:</strong> {alert.message}</p>
        
        {alert.trigger_flags && alert.trigger_flags.length > 0 && (
          <div>
            <strong>Triggers:</strong>
            <ul>
              {alert.trigger_flags.map((flag, index) => (
                <li key={index}>{flag}</li>
              ))}
            </ul>
          </div>
        )}
        
        {alert.escalated_to && (
          <p><strong>Escalated to:</strong> {alert.escalated_to}</p>
        )}
      </div>
      
      <div className="alert-actions">
        {!showResolveForm ? (
          <button 
            className="btn-primary"
            onClick={() => setShowResolveForm(true)}
          >
            Resolve Alert
          </button>
        ) : (
          <div className="resolve-form">
            <textarea
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Resolution notes..."
              rows={3}
            />
            <div className="resolve-actions">
              <button 
                className="btn-primary"
                onClick={handleResolve}
                disabled={resolving}
              >
                {resolving ? 'Resolving...' : 'Confirm Resolution'}
              </button>
              <button 
                className="btn-secondary"
                onClick={() => setShowResolveForm(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
