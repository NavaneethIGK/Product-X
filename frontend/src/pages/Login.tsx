import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Typography from '@mui/material/Typography'
import Alert from '@mui/material/Alert'
import CircularProgress from '@mui/material/CircularProgress'
import Container from '@mui/material/Container'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('admin@productx.com')
  const [password, setPassword] = useState('admin123')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const getBackendUrl = () => {
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    if (isLocalhost) return '/api'
    return `http://${window.location.hostname}:8000`
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const backendUrl = getBackendUrl()
      const response = await fetch(`${backendUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Invalid credentials')
      }

      const data = await response.json()
      
      // Store token in localStorage
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('user_email', data.user_email)

      // Trigger storage event for other components
      window.dispatchEvent(new Event('auth-changed'))

      // Small delay to ensure state updates, then navigate
      setTimeout(() => {
        navigate('/ai-copilot', { replace: true })
      }, 100)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
      setLoading(false)
    }
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={10}
          sx={{
            p: 4,
            borderRadius: 3,
            backdropFilter: 'blur(10px)',
            background: 'rgba(255, 255, 255, 0.95)',
          }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 800,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 1,
              }}
            >
              📦 Product X
            </Typography>
            <Typography variant="subtitle1" sx={{ color: '#666', mb: 3 }}>
              Supply Chain AI Copilot
            </Typography>
          </Box>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Login Form */}
          <Box component="form" onSubmit={handleLogin}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              margin="normal"
              variant="outlined"
              disabled={loading}
              placeholder="admin@productx.com"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                },
              }}
            />

            <TextField
              fullWidth
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              variant="outlined"
              disabled={loading}
              placeholder="admin123"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                },
              }}
            />

            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={handleLogin}
              disabled={loading}
              sx={{
                mt: 3,
                py: 1.5,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                fontWeight: 700,
                fontSize: '1rem',
                borderRadius: 2,
                textTransform: 'none',
                '&:hover': {
                  boxShadow: '0 8px 24px rgba(102, 126, 234, 0.4)',
                },
                '&:disabled': {
                  background: '#ccc',
                },
              }}
            >
              {loading ? (
                <CircularProgress size={24} sx={{ color: 'white' }} />
              ) : (
                'Login'
              )}
            </Button>
          </Box>

          {/* Default Credentials Info */}
          <Box
            sx={{
              mt: 3,
              p: 2,
              bgcolor: '#f5f7fb',
              borderRadius: 2,
              border: '1px solid #e8eef8',
            }}
          >
            <Typography variant="caption" sx={{ color: '#667eea', fontWeight: 700, display: 'block', mb: 1 }}>
              🔓 Demo Credentials
            </Typography>
            <Typography variant="caption" sx={{ color: '#1a1a2e', display: 'block', fontFamily: 'monospace' }}>
              Email: <strong>admin@productx.com</strong>
            </Typography>
            <Typography variant="caption" sx={{ color: '#1a1a2e', display: 'block', fontFamily: 'monospace' }}>
              Password: <strong>admin123</strong>
            </Typography>
          </Box>

          {/* Footer */}
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              textAlign: 'center',
              mt: 3,
              color: '#999',
            }}
          >
            🚀 Enterprise Supply Chain AI Powered by Groq + OpenAI
          </Typography>
        </Paper>
      </Container>
    </Box>
  )
}
