import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Login from './components/Login'
import Register from './components/Register'
import ClientDashboard from './components/ClientDashboard'
import CoachDashboard from './components/CoachDashboard'
import AdminPanel from './components/AdminPanel'
import Navigation from './components/Navigation'
import './App.css'

function ProtectedRoute({ children, allowedRoles = [] }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <div className="loading">Loading...</div>
  }
  
  if (!user) {
    return <Navigate to="/login" />
  }
  
  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" />
  }
  
  return children
}

function AppContent() {
  const { user } = useAuth()
  
  return (
    <div className="app">
      {user && <Navigation />}
      <main className="main-content">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          <Route path="/client" element={
            <ProtectedRoute allowedRoles={['client']}>
              <ClientDashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/coach" element={
            <ProtectedRoute allowedRoles={['coach', 'admin']}>
              <CoachDashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/admin" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminPanel />
            </ProtectedRoute>
          } />
          
          <Route path="/unauthorized" element={
            <div className="unauthorized">
              <h2>Unauthorized Access</h2>
              <p>You don't have permission to access this page.</p>
            </div>
          } />
          
          <Route path="/" element={
            user ? (
              user.role === 'client' ? <Navigate to="/client" /> :
              user.role === 'coach' ? <Navigate to="/coach" /> :
              user.role === 'admin' ? <Navigate to="/admin" /> :
              <Navigate to="/login" />
            ) : <Navigate to="/login" />
          } />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  )
}

export default App
