import React, { useEffect, useState } from 'react'
import { Routes, Route, Link, Navigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Topbar from './components/Topbar'
import Sidebar from './components/Sidebar'
import AICopilot from './pages/AICopilot'
import Login from './pages/Login'

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    setIsAuthenticated(!!token)
    setLoading(false)
  }, [])

  if (loading) return <Box>Loading...</Box>
  
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('auth_token'))

  // Listen for storage changes (when login/logout happens in another tab or component)
  useEffect(() => {
    const handleStorageChange = () => {
      setIsAuthenticated(!!localStorage.getItem('auth_token'))
    }

    const handleAuthChanged = () => {
      setIsAuthenticated(!!localStorage.getItem('auth_token'))
    }

    // Check auth on mount
    setIsAuthenticated(!!localStorage.getItem('auth_token'))

    // Listen for storage events (logout from another tab)
    window.addEventListener('storage', handleStorageChange)
    
    // Listen for custom auth-changed event
    window.addEventListener('auth-changed', handleAuthChanged)
    
    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('auth-changed', handleAuthChanged)
    }
  }, [])

  return (
    <Routes>
      {/* Public route */}
      <Route path="/login" element={<Login />} />

      {/* Protected routes */}
      <Route
        path="/*"
        element={
          isAuthenticated ? (
            <Box className="min-h-screen flex" sx={{ bgcolor: '#f8f9fa' }}>
              <Sidebar />
              <Box className="flex-1" sx={{ display: 'flex', flexDirection: 'column' }}>
                <Topbar />
                <Box component="main" sx={{ flex: 1, p: 0 }}>
                  <Routes>
                    <Route path="/" element={<AICopilot />} />
                    <Route path="/ai-copilot" element={<AICopilot />} />
                    <Route path="*" element={<div>Not Found — <Link to="/">Go home</Link></div>} />
                  </Routes>
                </Box>
              </Box>
            </Box>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  )
}
