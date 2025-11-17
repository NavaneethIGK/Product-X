import React, { useState, useEffect } from 'react'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'
import Grid from '@mui/material/Grid'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import { fetchAndAnalyzeCSV, DashboardMetrics } from '../utils/csvLoader'
import StatCard from '../components/StatCard'
import LineChart from '../components/LineChart'
import BarChart from '../components/BarChart'

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchAndAnalyzeCSV('/shipment_data_1M.csv')
      setMetrics(data)
      setLastUpdated(new Date())
    } catch (err) {
      setError('Failed to load CSV data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <CircularProgress />
        </Box>
      </Container>
    )
  }

  if (error) {
    return (
      <Container maxWidth="lg">
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      </Container>
    )
  }

  if (!metrics) {
    return (
      <Container maxWidth="lg">
        <Alert severity="warning" sx={{ mt: 2 }}>
          No data available
        </Alert>
      </Container>
    )
  }

  // Prepare chart data for route delays (top 10 routes)
  const topRoutes = Object.entries(metrics.routeMetrics)
    .sort(([, a], [, b]) => b.delayRate - a.delayRate)
    .slice(0, 10)

  // Prepare chart data for SKU delays (top 10 SKUs)
  const topSkus = Object.entries(metrics.skuMetrics)
    .sort(([, a], [, b]) => b.delayRate - a.delayRate)
    .slice(0, 10)

  // Status distribution data
  const statusData = [
    metrics.arrivedCount,
    metrics.inTransitCount,
    Math.max(0, metrics.delayedCount)
  ]

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
          Supply Chain Dashboard
        </Typography>
        <Button variant="outlined" size="small" onClick={loadData} disabled={loading}>
          Refresh Data
        </Button>
      </Box>

      {/* Key Performance Indicators */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Total Shipments" value={metrics.totalShipments.toLocaleString()} color="info.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="On-Time Rate" value={`${metrics.onTimePercentage}%`} color="success.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Delay Rate" value={`${metrics.delayPercentage}%`} color="warning.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Avg Delay" value={`${metrics.averageDelayDays} days`} color="error.main" />
        </Grid>
      </Grid>

      {/* Shipment Status Metrics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Arrived" value={metrics.arrivedCount.toLocaleString()} color="success.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="In Transit" value={metrics.inTransitCount.toLocaleString()} color="info.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Delayed" value={metrics.delayedCount.toLocaleString()} color="error.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Analysis Coverage"
            value={`${((metrics.totalShipments > 0 ? metrics.arrivedCount / metrics.totalShipments : 0) * 100).toFixed(1)}%`}
            color="secondary.main"
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} lg={6}>
          <BarChart
            title="Top Routes by Delay Rate"
            labels={topRoutes.map(([route]) => route.substring(0, 20))}
            datasets={[
              {
                label: 'Delay Rate (%)',
                data: topRoutes.map(([, metrics]) => Math.round(metrics.delayRate * 10) / 10),
                backgroundColor: '#ef5350'
              }
            ]}
            height={350}
          />
        </Grid>

        <Grid item xs={12} lg={6}>
          <BarChart
            title="Top SKUs by Delay Rate"
            labels={topSkus.map(([sku]) => sku)}
            datasets={[
              {
                label: 'Delay Rate (%)',
                data: topSkus.map(([, metrics]) => Math.round(metrics.delayRate * 10) / 10),
                backgroundColor: '#ffa726'
              }
            ]}
            height={350}
          />
        </Grid>
      </Grid>

      {/* Shipment Status Distribution */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} lg={6}>
          <LineChart
            title="Shipment Performance Trend"
            labels={['Arrived', 'In Transit', 'Delayed']}
            datasets={[
              {
                label: 'Shipment Count',
                data: statusData,
                borderColor: '#1976d2',
                backgroundColor: 'rgba(25, 118, 210, 0.1)',
                tension: 0.4
              }
            ]}
            height={350}
          />
        </Grid>

        <Grid item xs={12} lg={6}>
          <Box sx={{ p: 3, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontWeight: 600 }}>
              Data Summary
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Total Shipments Analyzed:</Typography>
                <Typography variant="body2" fontWeight={600}>
                  {metrics.totalShipments.toLocaleString()}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Successfully Delivered:</Typography>
                <Typography variant="body2" fontWeight={600} color="success.main">
                  {metrics.arrivedCount.toLocaleString()} ({metrics.onTimePercentage}%)
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Delayed Deliveries:</Typography>
                <Typography variant="body2" fontWeight={600} color="error.main">
                  {metrics.delayedCount.toLocaleString()} ({metrics.delayPercentage}%)
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">In Transit:</Typography>
                <Typography variant="body2" fontWeight={600} color="info.main">
                  {metrics.inTransitCount.toLocaleString()}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', pt: 1, borderTop: '1px solid #e0e0e0' }}>
                <Typography variant="body2">Average Delay:</Typography>
                <Typography variant="body2" fontWeight={600}>
                  {metrics.averageDelayDays} days
                </Typography>
              </Box>
            </Box>
          </Box>
        </Grid>
      </Grid>

      <Typography variant="caption" color="text.secondary">
        Real-time data from shipment_data_1M.csv • Last updated: {lastUpdated?.toLocaleString() || 'Never'}
      </Typography>
    </Container>
  )
}
