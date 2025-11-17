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
    <Container maxWidth="lg">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 1 }}>
          🤖 Supply Chain AI Copilot
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Ask questions about your supply chain, get AI-powered insights from 1M shipment analysis
        </Typography>
      </Box>

      {/* Status Alerts */}
      {backendStatus === 'offline' && (
        <Alert severity="warning" sx={{ mb: 2 }} onClose={() => {}}>
          Backend server is offline. Start it with: <code>python copilot_backend.py</code> in the terminal.
          <Button size="small" sx={{ ml: 2 }} onClick={checkBackendAndLoadModels}>
            Retry
          </Button>
        </Alert>
      )}

      {backendStatus === 'online' && (
        <Alert severity="success" sx={{ mb: 2 }}>
          ✓ Backend connected • Ready to chat
        </Alert>
      )}

      {/* Key Metrics */}
      {metrics && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="On-Time Rate"
              value={`${metrics.on_time_percentage}%`}
              color="success.main"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Delay Rate"
              value={`${metrics.delay_percentage}%`}
              color="warning.main"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Avg Delay"
              value={`${metrics.average_delay_days} days`}
              color="info.main"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Data Points"
              value={`${metrics.total_shipments.toLocaleString()}`}
              subtitle="shipments analyzed"
              color="secondary.main"
            />
          </Grid>
        </Grid>
      )}

      {/* Main Chat Interface */}
      <Grid container spacing={3}>
        {/* Chat */}
        <Grid item xs={12} lg={8}>
          {loading ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Initializing AI Copilot...
              </Typography>
            </Paper>
          ) : (
            <AICopilotChat apiUrl="http://localhost:8000" height={600} />
          )}
        </Grid>

        {/* Info Panel */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3 }} elevation={1}>
            <Typography variant="subtitle1" fontWeight={600} mb={2}>
              💡 What You Can Ask
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box>
                <Typography variant="body2" fontWeight={600} mb={0.5}>
                  Delay Analysis
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  "Which routes have the highest delay rates?" "What causes delays?"
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" fontWeight={600} mb={0.5}>
                  Route Performance
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  "Show me route statistics" "Which are our best routes?"
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" fontWeight={600} mb={0.5}>
                  Product Insights
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  "Which SKUs are problematic?" "Product performance analysis"
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" fontWeight={600} mb={0.5}>
                  Optimization
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  "How to improve delivery times?" "Recommendations"
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" fontWeight={600} mb={0.5}>
                  Predictions
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  "How accurate are your predictions?" "ETA confidence levels"
                </Typography>
              </Box>
            </Box>

            <Box sx={{ mt: 3, pt: 3, borderTop: '1px solid #e0e0e0' }}>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>
                🔧 System Info
              </Typography>
              <Typography variant="caption" display="block" color="text.secondary" mb={0.5}>
                <strong>Backend:</strong> {backendStatus === 'online' ? '✓ Online' : '✗ Offline'}
              </Typography>
              <Typography variant="caption" display="block" color="text.secondary" mb={0.5}>
                <strong>Data:</strong> 1M shipments
              </Typography>
              <Typography variant="caption" display="block" color="text.secondary">
                <strong>Models:</strong> ETA, Delay, Route Analytics
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  )
}
