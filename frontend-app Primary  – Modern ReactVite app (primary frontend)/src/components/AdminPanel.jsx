import { useState, useEffect } from 'react'
import { apiService } from '../services/api'

export default function AdminPanel() {
  const [overview, setOverview] = useState(null)
  const [users, setUsers] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchAdminData()
  }, [])

  const fetchAdminData = async () => {
    try {
      const [overviewRes, usersRes, analyticsRes] = await Promise.all([
        apiService.get('/dashboard/admin/overview'),
        apiService.get('/dashboard/admin/users'),
        apiService.get('/dashboard/admin/analytics?period=30')
      ])
      
      setOverview(overviewRes.data.overview)
      setUsers(usersRes.data.users)
      setAnalytics(analyticsRes.data.analytics)
    } catch (error) {
      console.error('Failed to fetch admin data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleToggleUserStatus = async (userId) => {
    try {
      await apiService.post(`/dashboard/admin/users/${userId}/toggle-status`)
      fetchAdminData()
    } catch (error) {
      console.error('Failed to toggle user status:', error)
    }
  }

  if (loading) {
    return <div className="loading">Loading admin panel...</div>
  }

  return (
    <div className="admin-panel">
      <div className="dashboard-header">
        <h1>Admin Panel</h1>
        <p>Platform management and analytics</p>
      </div>

      <div className="dashboard-tabs">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={activeTab === 'users' ? 'active' : ''}
          onClick={() => setActiveTab('users')}
        >
          Users ({users.length})
        </button>
        <button 
          className={activeTab === 'analytics' ? 'active' : ''}
          onClick={() => setActiveTab('analytics')}
        >
          Analytics
        </button>
      </div>

      <div className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="overview-grid">
            <div className="stat-card">
              <h3>Total Users</h3>
              <div className="stat-number">{overview?.total_users || 0}</div>
            </div>
            
            <div className="stat-card">
              <h3>Total Clients</h3>
              <div className="stat-number">{overview?.total_clients || 0}</div>
            </div>
            
            <div className="stat-card">
              <h3>Total Coaches</h3>
              <div className="stat-number">{overview?.total_coaches || 0}</div>
            </div>
            
            <div className="stat-card">
              <h3>New Users Today</h3>
              <div className="stat-number">{overview?.new_users_today || 0}</div>
            </div>
            
            <div className="stat-card">
              <h3>Active Sessions</h3>
              <div className="stat-number">{overview?.active_sessions || 0}</div>
            </div>
            
            <div className="stat-card revenue">
              <h3>Total Revenue</h3>
              <div className="stat-number">${overview?.total_revenue?.toFixed(2) || '0.00'}</div>
            </div>
            
            <div className="stat-card revenue">
              <h3>Monthly Revenue</h3>
              <div className="stat-number">${overview?.monthly_revenue?.toFixed(2) || '0.00'}</div>
            </div>
            
            <div className="stat-card alert">
              <h3>Active Crisis Alerts</h3>
              <div className="stat-number">{overview?.active_crisis_alerts || 0}</div>
            </div>

            <div className="dashboard-card full-width">
              <h2>User Growth (Last 7 Days)</h2>
              <div className="growth-chart">
                {overview?.user_growth?.map((day) => (
                  <div key={day.date} className="growth-item">
                    <span className="growth-date">{new Date(day.date).toLocaleDateString()}</span>
                    <span className="growth-count">{day.count} users</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="users-section">
            <div className="users-filters">
              <select onChange={(e) => console.log('Filter by role:', e.target.value)}>
                <option value="">All Roles</option>
                <option value="client">Clients</option>
                <option value="coach">Coaches</option>
                <option value="admin">Admins</option>
              </select>
              
              <select onChange={(e) => console.log('Filter by status:', e.target.value)}>
                <option value="active">Active Users</option>
                <option value="inactive">Inactive Users</option>
                <option value="">All Users</option>
              </select>
            </div>

            <div className="users-table">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td>{user.first_name} {user.last_name}</td>
                      <td>{user.email}</td>
                      <td>
                        <span className={`role-badge ${user.role}`}>
                          {user.role}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>{new Date(user.created_at).toLocaleDateString()}</td>
                      <td>
                        <button 
                          className={`btn-sm ${user.is_active ? 'btn-danger' : 'btn-success'}`}
                          onClick={() => handleToggleUserStatus(user.id)}
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="analytics-section">
            <div className="analytics-grid">
              <div className="analytics-card">
                <h3>Revenue Trends</h3>
                <div className="chart-placeholder">
                  {analytics?.revenue?.map((item) => (
                    <div key={item.date} className="chart-item">
                      <span>{item.date}</span>
                      <span>${item.amount.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="analytics-card">
                <h3>Session Activity</h3>
                <div className="chart-placeholder">
                  {analytics?.sessions?.map((item) => (
                    <div key={item.date} className="chart-item">
                      <span>{item.date}</span>
                      <span>{item.count} sessions</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="analytics-card">
                <h3>User Registrations</h3>
                <div className="chart-placeholder">
                  {analytics?.registrations?.map((item) => (
                    <div key={item.date} className="chart-item">
                      <span>{item.date}</span>
                      <span>{item.count} users</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="analytics-card">
                <h3>Crisis Alerts</h3>
                <div className="chart-placeholder">
                  {analytics?.crisis_alerts?.map((item) => (
                    <div key={item.date} className="chart-item">
                      <span>{item.date}</span>
                      <span>{item.count} alerts</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
