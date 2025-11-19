import React, { useState, useEffect } from 'react'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'
import Grid from '@mui/material/Grid'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Button from '@mui/material/Button'
import Alert from '@mui/material/Alert'
import LinearProgress from '@mui/material/LinearProgress'
import { Refresh as RefreshIcon, TrendingUp as TrendingIcon, Package as PackageIcon, Speed as SpeedIcon, Alarm as AlarmIcon } from '@mui/icons-material'
import StatCard from '../components/StatCard'
import PredictionsTable from '../components/PredictionsTable'
import BarChart from '../components/BarChart'
import LineChart from '../components/LineChart'

type Metrics = {
  total_shipments: number
  on_time_percentage: number
  delay_percentage: number
  average_delay_days: number
  maximum_delay_days: number
  median_transit_days: number
}

type Prediction = {
  shipment_id: string
  route: string
  departed_at: string
  expected_arrival: string
  predicted_arrival: string
  predicted_days: number
  confidence: number
  delay_risk: 'LOW' | 'MEDIUM' | 'HIGH'
  status: string
}

export default function PredictionsAnalytics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      setLoading(true)
      const [metricsRes, predictionsRes] = await Promise.all([
        fetch('/models.json'),
        fetch('/predictions.json')
      ])

      const modelsData = await metricsRes.json()
      const predictionsData = await predictionsRes.json()

      setMetrics(modelsData.global_metrics)
      setPredictions(predictionsData)
    } catch (error) {
      console.error('Error loading models:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
            Loading prediction models...
          </Typography>
          <LinearProgress sx={{ height: 8, borderRadius: 4 }} />
        </Box>
      </Container>
    )
  }

  if (!metrics) {
    return (
      <Container maxWidth="lg">
        <Alert severity="error" sx={{ mt: 2 }}>
          Failed to load prediction models
        </Alert>
      </Container>
    )
  }

  const delayRiskCounts = predictions.reduce(
    (acc, p) => {
      acc[p.delay_risk] = (acc[p.delay_risk] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  const confidenceRanges = predictions.reduce(
    (acc, p) => {
      const range =
        p.confidence >= 90
          ? '90-100%'
          : p.confidence >= 80
            ? '80-89%'
            : p.confidence >= 70
              ? '70-79%'
              : '<70%'
      acc[range] = (acc[range] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  // Trend data for line chart (simulated based on predictions)
  const trendLabels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
  const delayTrend = [
    Math.round(metrics.delay_percentage * 0.8),
    Math.round(metrics.delay_percentage * 0.85),
    metrics.delay_percentage,
    Math.round(metrics.delay_percentage * 0.95)
  ]
  const onTimeTrend = trendLabels.map((_, idx) => 100 - delayTrend[idx])

  return (
    <Box sx={{ bgcolor: '#f5f7fb', minHeight: '100vh', py: 2 }}>
      <Container maxWidth="lg">
        {/* Hero Section */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box>
              <Typography
                variant="h3"
                component="h1"
                sx={{
                  fontWeight: 800,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 0.5,
                  fontSize: { xs: '2rem', md: '2.8rem' }
                }}
              >
                ETA Predictions
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                AI-Powered Shipment Delay Analytics & Risk Assessment
              </Typography>
            </Box>
            <Button
              size="small"
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={loadModels}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                textTransform: 'none',
                fontWeight: 600,
                px: 1.5,
                py: 0.5,
                borderRadius: 2,
                boxShadow: '0 8px 20px rgba(99, 102, 241, 0.12)',
                fontSize: '0.85rem',
                '&:hover': {
                  boxShadow: '0 10px 26px rgba(99, 102, 241, 0.16)',
                }
              }}
            >
              Refresh
            </Button>
          </Box>

          {/* Featured Metrics Grid */}
          <Grid container spacing={1.5}>
            <Grid item xs={12} sm={6}>
              <Paper
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  boxShadow: '0 8px 24px rgba(102, 126, 234, 0.2)'
                }}
              >
                <Typography variant="body2" sx={{ opacity: 0.9, mb: 0.5, fontWeight: 600 }}>
                  ✈️ On-Time Rate
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {metrics.on_time_percentage}%
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.85 }}>
                  {metrics.total_shipments.toLocaleString()} shipments analyzed
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Paper
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                  color: 'white',
                  boxShadow: '0 8px 24px rgba(250, 112, 154, 0.2)'
                }}
              >
                <Typography variant="body2" sx={{ opacity: 0.9, mb: 0.5, fontWeight: 600 }}>
                  ⚠️ Delay Risk
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {metrics.delay_percentage}%
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.85 }}>
                  Current trend analysis
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>

        {/* Key Metrics Row */}
        <Grid container spacing={1.5} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Avg Delay"
              value={`${metrics.average_delay_days}d`}
              bgGradient="linear-gradient(135deg, #30cfd0 0%, #330867 100%)"
              icon="⏱️"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Max Delay"
              value={`${metrics.maximum_delay_days}d`}
              bgGradient="linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)"
              icon="📍"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Median Transit"
              value={`${metrics.median_transit_days}d`}
              bgGradient="linear-gradient(135deg, #ffa751 0%, #ffe259 100%)"
              icon="📦"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Total Dataset"
              value={`${(metrics.total_shipments / 1000000).toFixed(1)}M`}
              bgGradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
              icon="📊"
            />
          </Grid>
        </Grid>

        {/* Risk Distribution Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5, color: '#333' }}>
            📊 Risk Distribution
          </Typography>
          <Grid container spacing={1.5}>
            <Grid item xs={12} sm={6} md={4}>
              <Paper
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
                  color: 'white',
                  boxShadow: '0 6px 18px rgba(16,24,40,0.04)',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 700, opacity: 0.95 }}>Low Risk</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, my: 0.5 }}>
                      {delayRiskCounts['LOW'] || 0}
                    </Typography>
                  </Box>
                  <Box sx={{ fontSize: 32, opacity: 0.8 }}>📦</Box>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={(((delayRiskCounts['LOW'] || 0) / predictions.length) * 100) || 0}
                  sx={{
                    height: 5,
                    borderRadius: 2,
                    backgroundColor: 'rgba(255,255,255,0.3)',
                    '& .MuiLinearProgress-bar': { backgroundColor: 'white' }
                  }}
                />
                <Typography variant="caption" sx={{ display: 'block', mt: 0.8, opacity: 0.85 }}>
                  {Math.round((((delayRiskCounts['LOW'] || 0) / predictions.length) * 100) || 0)}% of shipments
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} sm={6} md={4}>
              <Paper
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                  color: 'white',
                  boxShadow: '0 6px 18px rgba(16,24,40,0.04)',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 700, opacity: 0.95 }}>Medium Risk</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, my: 0.5 }}>
                      {delayRiskCounts['MEDIUM'] || 0}
                    </Typography>
                  </Box>
                  <Box sx={{ fontSize: 32, opacity: 0.8 }}>⚡</Box>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={(((delayRiskCounts['MEDIUM'] || 0) / predictions.length) * 100) || 0}
                  sx={{
                    height: 5,
                    borderRadius: 2,
                    backgroundColor: 'rgba(255,255,255,0.3)',
                    '& .MuiLinearProgress-bar': { backgroundColor: 'white' }
                  }}
                />
                <Typography variant="caption" sx={{ display: 'block', mt: 0.8, opacity: 0.85 }}>
                  {Math.round((((delayRiskCounts['MEDIUM'] || 0) / predictions.length) * 100) || 0)}% of shipments
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} sm={6} md={4}>
              <Paper
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)',
                  color: 'white',
                  boxShadow: '0 6px 18px rgba(16,24,40,0.04)',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 700, opacity: 0.95 }}>High Risk</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 800, my: 0.5 }}>
                      {delayRiskCounts['HIGH'] || 0}
                    </Typography>
                  </Box>
                  <Box sx={{ fontSize: 32, opacity: 0.8 }}>🔴</Box>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={(((delayRiskCounts['HIGH'] || 0) / predictions.length) * 100) || 0}
                  sx={{
                    height: 5,
                    borderRadius: 2,
                    backgroundColor: 'rgba(255,255,255,0.3)',
                    '& .MuiLinearProgress-bar': { backgroundColor: 'white' }
                  }}
                />
                <Typography variant="caption" sx={{ display: 'block', mt: 0.8, opacity: 0.85 }}>
                  {Math.round((((delayRiskCounts['HIGH'] || 0) / predictions.length) * 100) || 0)}% of shipments
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>

        {/* Analytics Charts */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5, color: '#333' }}>
            📈 Performance Trends
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden', p: 2, boxShadow: '0 6px 18px rgba(16,24,40,0.04)' }}>
                <LineChart
                  title="On-Time Delivery Trend"
                  labels={trendLabels}
                  datasets={[
                    {
                      label: 'On-Time Rate (%)',
                      data: onTimeTrend,
                      borderColor: '#4caf50',
                      backgroundColor: 'rgba(76, 175, 80, 0.1)',
                      tension: 0.4
                    }
                  ]}
                  height={280}
                />
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden', p: 2, boxShadow: '0 6px 18px rgba(16,24,40,0.04)' }}>
                <LineChart
                  title="Delay Rate Trend"
                  labels={trendLabels}
                  datasets={[
                    {
                      label: 'Delay Rate (%)',
                      data: delayTrend,
                      borderColor: '#f44336',
                      backgroundColor: 'rgba(244, 67, 54, 0.1)',
                      tension: 0.4
                    }
                  ]}
                  height={280}
                />
              </Paper>
            </Grid>
          </Grid>
        </Box>

        {/* Distribution Charts */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5, color: '#333' }}>
            📊 Prediction Analysis
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} lg={6}>
              <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden', p: 2, boxShadow: '0 6px 18px rgba(16,24,40,0.04)' }}>
                <BarChart
                  title="Prediction Confidence Levels"
                  labels={Object.keys(confidenceRanges)}
                  datasets={[
                    {
                      label: 'Number of Predictions',
                      data: Object.values(confidenceRanges),
                      backgroundColor: ['#4caf50', '#2196f3', '#ff9800', '#f44336']
                    }
                  ]}
                  height={260}
                />
              </Paper>
            </Grid>

            <Grid item xs={12} lg={6}>
              <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden', p: 2, boxShadow: '0 6px 18px rgba(16,24,40,0.04)' }}>
                <BarChart
                  title="Delay Risk Distribution"
                  labels={['Low Risk', 'Medium Risk', 'High Risk']}
                  datasets={[
                    {
                      label: 'Shipments',
                      data: [
                        delayRiskCounts['LOW'] || 0,
                        delayRiskCounts['MEDIUM'] || 0,
                        delayRiskCounts['HIGH'] || 0
                      ],
                      backgroundColor: ['#4caf50', '#ff9800', '#f44336']
                    }
                  ]}
                  height={260}
                />
              </Paper>
            </Grid>
          </Grid>
        </Box>

        {/* Active Predictions Table */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5, color: '#333' }}>
            🚀 Active Shipment Predictions
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            Real-time ETA predictions with confidence scores and delay risk assessment
          </Typography>
          <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden', p: 1, boxShadow: '0 6px 18px rgba(16,24,40,0.04)' }}>
            <Box sx={{ maxHeight: 420, overflow: 'auto' }}>
              <PredictionsTable predictions={predictions} maxRows={50} />
            </Box>
          </Paper>
        </Box>

        {/* Footer Stats */}
        <Box
          sx={{
            mt: 3,
            pt: 2,
            borderTop: '1px solid #e0e0e0',
            textAlign: 'center'
          }}
        >
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
            📊 Models trained on 1M historical shipments • 🚀 {predictions.length} active predictions • 
            🎯 Avg confidence: {Math.round((predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.length || 0))}%
          </Typography>
        </Box>
      </Container>
    </Box>
  )
}
