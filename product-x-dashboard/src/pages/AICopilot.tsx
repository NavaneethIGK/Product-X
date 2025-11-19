import React, { useState, useEffect } from 'react'
import Typography from '@mui/material/Typography'
import Grid from '@mui/material/Grid'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import AICopilotChat from '../components/AICopilotChat'
import StatCard from '../components/StatCard'

type Metrics = {
  total_shipments: number
  on_time_percentage: number
  delay_percentage: number
  average_delay_days: number
  maximum_delay_days: number
  median_transit_days: number
}

export default function AICopilot() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkBackendAndLoadModels()
  }, [])

  const checkBackendAndLoadModels = async () => {
    try {
      setLoading(true)

      // Check backend health
      const healthRes = await fetch('http://localhost:8000/health')
      if (healthRes.ok) {
        setBackendStatus('online')
      } else {
        setBackendStatus('offline')
      }

      // Load models
      const modelsRes = await fetch('/models.json')
      const modelsData = await modelsRes.json()
      setMetrics(modelsData.global_metrics)
    } catch (error) {
      console.error('Error:', error)
      setBackendStatus('offline')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ bgcolor: '#f5f7fb', display: 'flex', flexDirection: 'column', p: 2 }}>
      {/* Header */}
      <Box sx={{ mb: 1 }}>
        <Typography 
          variant="h5" 
          component="h1" 
          sx={{ 
            fontWeight: 800, 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontSize: '1.8rem'
          }}
        >
          🤖 Supply Chain AI Copilot
        </Typography>
      </Box>

      {/* Status Alert */}
      {backendStatus === 'offline' && (
        <Alert severity="warning" sx={{ mb: 1, borderRadius: 2, fontSize: '0.85rem' }} onClose={() => {}}>
          Backend offline. Start: <code>python copilot_backend.py</code>
          <Button size="small" sx={{ ml: 1 }} onClick={checkBackendAndLoadModels}>
            Retry
          </Button>
        </Alert>
      )}

      {backendStatus === 'online' && (
        <Alert severity="success" sx={{ mb: 1, borderRadius: 2, fontSize: '0.85rem' }}>
          ✓ Backend online • Ready to chat
        </Alert>
      )}

      {/* Main Content - No Scroll */}
      <Grid container spacing={1} sx={{ flex: 1, overflow: 'hidden' }}>
        {/* Left Panel - Metrics & Info */}
        <Grid item xs={12} md={4} sx={{ overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 1 }}>
          {/* Key Metrics */}
          {metrics && (
            <>
              <Grid container spacing={1}>
                <Grid item xs={12} sm={6} md={12}>
                  <StatCard
                    title="On-Time Rate"
                    value={`${metrics.on_time_percentage}%`}
                    bgGradient="linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)"
                    icon="✈️"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={12}>
                  <StatCard
                    title="Delay Rate"
                    value={`${metrics.delay_percentage}%`}
                    bgGradient="linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
                    icon="⚠️"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={12}>
                  <StatCard
                    title="Avg Delay"
                    value={`${metrics.average_delay_days} days`}
                    bgGradient="linear-gradient(135deg, #30cfd0 0%, #330867 100%)"
                    icon="⏱️"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={12}>
                  <StatCard
                    title="Data Points"
                    value={`${metrics.total_shipments.toLocaleString()}`}
                    bgGradient="linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)"
                    subtitle="analyzed"
                    icon="📊"
                  />
                </Grid>
              </Grid>

              {/* Info Box */}
              <Paper elevation={3} sx={{ p: 1.5, borderRadius: 2, flexShrink: 0 }}>
                <Typography variant="body2" fontWeight={700} mb={1} sx={{ color: '#333', fontSize: '0.85rem' }}>
                  💡 Quick Tips
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.8 }}>
                  <Box sx={{ p: 1, bgcolor: 'rgba(132, 250, 176, 0.1)', borderRadius: 1 }}>
                    <Typography variant="caption" fontWeight={700} color="#333" sx={{ fontSize: '0.75rem' }}>
                      📍 Delay Analysis
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ fontSize: '0.7rem', mt: 0.2 }}>
                      "Which routes delay most?"
                    </Typography>
                  </Box>

                  <Box sx={{ p: 1, bgcolor: 'rgba(250, 112, 154, 0.1)', borderRadius: 1 }}>
                    <Typography variant="caption" fontWeight={700} color="#333" sx={{ fontSize: '0.75rem' }}>
                      🛣️ Route Performance
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ fontSize: '0.7rem', mt: 0.2 }}>
                      "Show route stats"
                    </Typography>
                  </Box>

                  <Box sx={{ p: 1, bgcolor: 'rgba(48, 207, 208, 0.1)', borderRadius: 1 }}>
                    <Typography variant="caption" fontWeight={700} color="#333" sx={{ fontSize: '0.75rem' }}>
                      📦 Problem SKUs
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ fontSize: '0.7rem', mt: 0.2 }}>
                      "Problematic products?"
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ mt: 1.5, pt: 1.5, borderTop: '1px solid #e8eef8' }}>
                  <Typography variant="caption" display="block" color="text.secondary" mb={0.3} sx={{ fontSize: '0.7rem', fontWeight: 600 }}>
                    <strong>Backend:</strong> {backendStatus === 'online' ? <span style={{ color: '#4caf50' }}>✓ Online</span> : <span style={{ color: '#f44336' }}>✗ Offline</span>}
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                    <strong>Data:</strong> 1M shipments
                  </Typography>
                </Box>
              </Paper>
            </>
          )}
        </Grid>

        {/* Right Panel - Chat */}
        <Grid item xs={12} md={8} sx={{ overflow: 'hidden', display: 'flex', alignItems: 'flex-start' }}>
          {loading ? (
            <Paper sx={{ p: 2, textAlign: 'center', borderRadius: 2, width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography variant="caption" color="text.secondary">
                Initializing AI Copilot...
              </Typography>
            </Paper>
          ) : (
            <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden', width: '100%', p: 1.5 }}>
              <AICopilotChat apiUrl="http://localhost:8000" height={520} />
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}
