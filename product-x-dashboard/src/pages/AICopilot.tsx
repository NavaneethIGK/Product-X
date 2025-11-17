import React, { useState, useEffect } from 'react'
import Container from '@mui/material/Container'
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
    <Box sx={{ bgcolor: '#f5f7fb', minHeight: '100vh', py: 5 }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ mb: 5 }}>
          <Typography 
            variant="h3" 
            component="h1" 
            sx={{ 
              fontWeight: 800, 
              mb: 1.5,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontSize: { xs: '2rem', md: '2.8rem' }
            }}
          >
            🤖 Supply Chain AI Copilot
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 500, maxWidth: 600, fontSize: '1.05rem' }}>
            Ask questions about your supply chain, get AI-powered insights from 1M shipment analysis
          </Typography>
        </Box>

        {/* Status Alerts */}
        {backendStatus === 'offline' && (
          <Alert severity="warning" sx={{ mb: 3, borderRadius: 2, fontSize: '0.95rem' }} onClose={() => {}}>
            Backend server is offline. Start it with: <code>python copilot_backend.py</code> in the terminal.
            <Button size="small" sx={{ ml: 2 }} onClick={checkBackendAndLoadModels}>
              Retry
            </Button>
          </Alert>
        )}

        {backendStatus === 'online' && (
          <Alert severity="success" sx={{ mb: 3, borderRadius: 2, fontSize: '0.95rem' }}>
            ✓ Backend connected • Ready to chat
          </Alert>
        )}

        {/* Key Metrics */}
        {metrics && (
          <Grid container spacing={3} sx={{ mb: 5 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="On-Time Rate"
                value={`${metrics.on_time_percentage}%`}
                bgGradient="linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)"
                icon="✈️"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Delay Rate"
                value={`${metrics.delay_percentage}%`}
                bgGradient="linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
                icon="⚠️"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Avg Delay"
                value={`${metrics.average_delay_days} days`}
                bgGradient="linear-gradient(135deg, #30cfd0 0%, #330867 100%)"
                icon="⏱️"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Data Points"
                value={`${metrics.total_shipments.toLocaleString()}`}
                bgGradient="linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)"
                subtitle="analyzed"
                icon="📊"
              />
            </Grid>
          </Grid>
        )}

        {/* Main Chat Interface */}
        <Grid container spacing={4}>
          {/* Chat */}
          <Grid item xs={12} lg={8}>
            {loading ? (
              <Paper sx={{ p: 6, textAlign: 'center', borderRadius: 3 }}>
                <CircularProgress sx={{ mb: 3 }} />
                <Typography variant="body2" color="text.secondary">
                  Initializing AI Copilot...
                </Typography>
              </Paper>
            ) : (
              <Paper elevation={4} sx={{ borderRadius: 3, overflow: 'hidden', height: '600px' }}>
                <AICopilotChat apiUrl="http://localhost:8000" height={600} />
              </Paper>
            )}
          </Grid>

          {/* Info Panel */}
          <Grid item xs={12} lg={4}>
            <Paper elevation={4} sx={{ p: 4, borderRadius: 3 }}>
              <Typography variant="subtitle1" fontWeight={800} mb={3} sx={{ color: '#333', fontSize: '1.1rem' }}>
                💡 What You Can Ask
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                <Box sx={{ p: 2.5, bgcolor: 'rgba(132, 250, 176, 0.1)', borderRadius: 2 }}>
                  <Typography variant="body2" fontWeight={700} mb={0.8} color="#333">
                    📍 Delay Analysis
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.85rem', lineHeight: 1.5 }}>
                    "Which routes have the highest delay rates?" "What causes delays?"
                  </Typography>
                </Box>

                <Box sx={{ p: 2.5, bgcolor: 'rgba(250, 112, 154, 0.1)', borderRadius: 2 }}>
                  <Typography variant="body2" fontWeight={700} mb={0.8} color="#333">
                    🛣️ Route Performance
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.85rem', lineHeight: 1.5 }}>
                    "Show me route statistics" "Which are our best routes?"
                  </Typography>
                </Box>

                <Box sx={{ p: 2.5, bgcolor: 'rgba(48, 207, 208, 0.1)', borderRadius: 2 }}>
                  <Typography variant="body2" fontWeight={700} mb={0.8} color="#333">
                    📦 Product Insights
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.85rem', lineHeight: 1.5 }}>
                    "Which SKUs are problematic?" "Product performance analysis"
                  </Typography>
                </Box>

                <Box sx={{ p: 2.5, bgcolor: 'rgba(168, 237, 234, 0.1)', borderRadius: 2 }}>
                  <Typography variant="body2" fontWeight={700} mb={0.8} color="#333">
                    ⚡ Optimization
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.85rem', lineHeight: 1.5 }}>
                    "How to improve delivery times?" "Recommendations"
                  </Typography>
                </Box>

                <Box sx={{ p: 2.5, bgcolor: 'rgba(102, 126, 234, 0.1)', borderRadius: 2 }}>
                  <Typography variant="body2" fontWeight={700} mb={0.8} color="#333">
                    🎯 Predictions
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.85rem', lineHeight: 1.5 }}>
                    "How accurate are predictions?" "ETA confidence levels"
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ mt: 4, pt: 4, borderTop: '2px solid #f0f0f0' }}>
                <Typography variant="subtitle2" fontWeight={800} mb={2.5} sx={{ color: '#333', fontSize: '1rem' }}>
                  🔧 System Info
                </Typography>
                <Box sx={{ space: 1 }}>
                  <Typography variant="caption" display="block" color="text.secondary" mb={1.2} sx={{ fontSize: '0.9rem' }}>
                    <strong>Backend:</strong> {backendStatus === 'online' ? <span style={{ color: '#4caf50', fontWeight: 700 }}>✓ Online</span> : <span style={{ color: '#f44336', fontWeight: 700 }}>✗ Offline</span>}
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary" mb={1.2} sx={{ fontSize: '0.9rem' }}>
                    <strong>Data:</strong> 1M shipments
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary" sx={{ fontSize: '0.9rem' }}>
                    <strong>Models:</strong> ETA, Delay, Route Analytics
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}
