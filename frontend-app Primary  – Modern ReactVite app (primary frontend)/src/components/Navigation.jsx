import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Navigation() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const handleLogout = async () => {
    await logout()
  }

  const isActive = (path) => location.pathname === path

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <Link to="/">Purposeful Live</Link>
      </div>
      
      <div className="nav-links">
        {user?.role === 'client' && (
          <Link 
            to="/client" 
            className={isActive('/client') ? 'active' : ''}
          >
            Dashboard
          </Link>
        )}
        
        {(user?.role === 'coach' || user?.role === 'admin') && (
          <Link 
            to="/coach" 
            className={isActive('/coach') ? 'active' : ''}
          >
            Coach Dashboard
          </Link>
        )}
        
        {user?.role === 'admin' && (
          <Link 
            to="/admin" 
            className={isActive('/admin') ? 'active' : ''}
          >
            Admin Panel
          </Link>
        )}
      </div>
      
      <div className="nav-user">
        <span className="user-info">
          {user?.first_name} {user?.last_name} ({user?.role})
        </span>
        <button onClick={handleLogout} className="btn-secondary">
          Logout
        </button>
      </div>
    </nav>
  )
}
