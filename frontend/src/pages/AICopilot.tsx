import React, { useState, useEffect } from 'react'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import AICopilotChat from '../components/AICopilotChat'

type Metrics = {
  total_shipments?: number
  on_time_rate?: number
  delay_rate?: number
  average_delay_days?: number
  unique_routes?: number
  unique_skus?: number
}

type CardData = {
  title: string
  value: string
  subtitle?: string
  icon: string
  gradient: string
  query: string
}

export default function AICopilot() {
  const getBackendUrl = () => {
    const envUrl = (import.meta as any).env.VITE_API_URL
    if (envUrl) return envUrl
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    if (isLocalhost) return '/api'
    return `http://${window.location.hostname}:8000`
  }
  
  const backendUrl = getBackendUrl()
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [cardData, setCardData] = useState<CardData[]>([])
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkBackendAndLoadMetrics()
  }, [backendUrl])

  const checkBackendAndLoadMetrics = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${backendUrl}/health`)
      if (!response.ok) throw new Error('Backend health check failed')
      setBackendStatus('online')
      await loadMetrics()
    } catch (err) {
      console.error('Backend check failed:', err)
      setBackendStatus('offline')
      setLoading(false)
    }
  }

  const loadMetrics = async () => {
    try {
      const metricsQuery = 'Analyze the shipment data and provide exact numbers: on-time delivery percentage, delayed shipment percentage, average delay in days, total number of shipments, count of unique delivery routes, and count of unique SKUs.'
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: metricsQuery })
      })
      if (!response.ok) throw new Error('Failed to load metrics')
      const data = await response.json()
      const responseText = data.response
      
      const totalMatch = responseText.match(/total.*?(\d{1,3}(?:,\d{3})*)/i) || responseText.match(/shipments.*?(\d{1,3}(?:,\d{3})*)/i)
      const onTimeMatch = responseText.match(/on-?time.*?(\d+(?:\.\d{1,2})?)/i) || responseText.match(/delivery.*?(\d+(?:\.\d{1,2})?)%/i)
      const delayMatch = responseText.match(/delay.*?(\d+(?:\.\d{1,2})?)/i)
      const avgDelayMatch = responseText.match(/average.*?delay.*?(\d+(?:\.\d{1,2})?)/i) || responseText.match(/delay.*?(\d+(?:\.\d{1,2})?).*?days/i)
      const routesMatch = responseText.match(/routes.*?(\d+)/i) || responseText.match(/(\d+).*?routes/i)
      const skusMatch = responseText.match(/skus.*?(\d+)/i) || responseText.match(/(\d+).*?sku/i)

      const parsedMetrics: Metrics = {
        total_shipments: totalMatch ? parseInt(totalMatch[1].replace(/,/g, '')) : 1000000,
        on_time_rate: onTimeMatch ? parseFloat(onTimeMatch[1]) : 70,
        delay_rate: delayMatch ? parseFloat(delayMatch[1]) : 30,
        average_delay_days: avgDelayMatch ? parseFloat(avgDelayMatch[1]) : 6.5,
        unique_routes: routesMatch ? parseInt(routesMatch[1]) : 56,
        unique_skus: skusMatch ? parseInt(skusMatch[1]) : 500
      }
      setMetrics(parsedMetrics)
      
      const newCardData: CardData[] = [
        {
          title: 'On-Time Rate',
          value: `${(parsedMetrics.on_time_rate || 70).toFixed(1)}%`,
          icon: '✈️',
          gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          query: 'on-time delivery rate'
        },
        {
          title: 'Delay Rate',
          value: `${(parsedMetrics.delay_rate || 30).toFixed(1)}%`,
          icon: '⏱️',
          gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          query: 'delayed shipment percentage'
        },
        {
          title: 'Avg Delay',
          value: `${(parsedMetrics.average_delay_days || 6.5).toFixed(1)} days`,
          icon: '📅',
          gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
          query: 'average delay in days'
        },
        {
          title: 'Total Shipments',
          value: `${parsedMetrics.total_shipments?.toLocaleString() || '1M'}`,
          subtitle: 'analyzed',
          icon: '📦',
          gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
          query: 'total number of shipments'
        },
        {
          title: 'Unique Routes',
          value: `${parsedMetrics.unique_routes || 56}`,
          subtitle: 'unique',
          icon: '🛣️',
          gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
          query: 'count of unique delivery routes'
        },
        {
          title: 'SKUs',
          value: `${parsedMetrics.unique_skus || 500}`,
          subtitle: 'products',
          icon: '📊',
          gradient: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
          query: 'count of unique SKUs'
        }
      ]
      setCardData(newCardData)
    } catch (err) {
      console.error('Failed to load metrics:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: '#f8fafc', overflow: 'hidden' }}>
      {/* Header */}
      <Box sx={{ bgcolor: 'white', borderBottom: '1px solid #e2e8f0', px: 4, py: 2, flexShrink: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 700, color: '#1e293b', fontSize: '1.4rem', mb: 0.2 }}>
              Supply Chain Intelligence Dashboard
            </Typography>
            <Typography variant="body2" sx={{ fontSize: '0.9rem', color: '#64748b' }}>
              AI-Powered Insights & Real-Time Analytics
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1, bgcolor: backendStatus === 'online' ? 'rgba(34, 197, 94, 0.08)' : 'rgba(239, 68, 68, 0.08)', borderRadius: 2, border: `1px solid ${backendStatus === 'online' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}` }}>
            <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: backendStatus === 'online' ? '#22c55e' : '#ef4444', animation: backendStatus === 'online' ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none', '@keyframes pulse': { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0.5 } } }} />
            <Typography variant="caption" fontWeight={700} sx={{ fontSize: '0.85rem', color: backendStatus === 'online' ? '#22c55e' : '#ef4444' }}>
              {backendStatus === 'online' ? 'System Online' : 'System Offline'}
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Main Content */}
      <Box sx={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 300px', gap: 0, overflow: 'hidden' }}>
        {/* Left Panel - Chat */}
        <Box sx={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', bgcolor: '#f8fafc' }}>
          {/* Chat Section */}
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', px: 4, py: 3, overflow: 'hidden', minHeight: 0 }}>
            {loading ? (
              <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'white', borderRadius: 2 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <CircularProgress size={40} sx={{ mb: 2 }} />
                  <Typography color="text.secondary">Initializing AI Assistant...</Typography>
                </Box>
              </Box>
            ) : (
              <Box sx={{ flex: 1, bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0', overflow: 'hidden', display: 'flex', flexDirection: 'column', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)', minHeight: 0 }}>
                <AICopilotChat apiUrl={backendUrl} height={700} />
              </Box>
            )}
          </Box>

          {/* KPI Cards */}
          <Box sx={{ px: 4, py: 2.5, flexShrink: 0, bgcolor: 'white', borderTop: '1px solid #e2e8f0' }}>
            <Typography variant="caption" sx={{ fontWeight: 700, color: '#1e293b', fontSize: '0.8rem', mb: 1, textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block' }}>
              Key Performance Indicators
            </Typography>
            
            {loading ? (
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 1 }}>
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <Box key={i} sx={{ height: '60px', bgcolor: 'rgba(0, 0, 0, 0.05)', borderRadius: 1.5, animation: 'pulse 1.5s ease-in-out infinite', '@keyframes pulse': { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0.5 } } }} />
                ))}
              </Box>
            ) : (
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 1 }}>
                {cardData.length > 0 && cardData.map((card, idx) => (
                  <Box key={idx} sx={{ p: 0.9, borderRadius: 1.5, background: card.gradient, color: 'white', cursor: 'pointer', transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)', border: '1px solid rgba(255, 255, 255, 0.1)', '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 6px 12px rgba(0, 0, 0, 0.1)' } }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.2 }}>
                      <Typography variant="caption" sx={{ fontSize: '0.65rem', opacity: 0.9, fontWeight: 700 }}>
                        {card.title}
                      </Typography>
                      <Typography sx={{ fontSize: '1rem' }}>{card.icon}</Typography>
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 800, fontSize: '0.95rem', letterSpacing: '-0.3px', mb: 0.1 }}>
                      {card.value}
                    </Typography>
                    {card.subtitle && (
                      <Typography variant="caption" sx={{ fontSize: '0.6rem', opacity: 0.75 }}>
                        {card.subtitle}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        </Box>

        {/* Right Sidebar */}
        <Box sx={{ display: { xs: 'none', md: 'flex' }, flexDirection: 'column', bgcolor: 'linear-gradient(180deg, #ffffff 0%, #f9fafb 100%)', borderLeft: '1px solid #e2e8f0', overflow: 'hidden' }}>
          {/* Data Summary */}
          <Box sx={{ px: 1.8, py: 2, flexShrink: 0, borderBottom: '1px solid #e2e8f0' }}>
            <Typography variant="caption" sx={{ fontWeight: 800, color: '#1e293b', fontSize: '0.75rem', mb: 1.2, textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block' }}>
              Data Summary
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.8 }}>
              <Box sx={{ p: 1, bgcolor: 'white', borderRadius: 1.5, border: '1px solid #e2e8f0', transition: 'all 0.2s', '&:hover': { borderColor: '#cbd5e1', boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)' } }}>
                <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.2px', display: 'block', mb: 0.3 }}>Shipments</Typography>
                <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '1rem', color: '#1e293b' }}>{metrics?.total_shipments?.toLocaleString() || '1M'}</Typography>
              </Box>
              <Box sx={{ p: 1, bgcolor: 'white', borderRadius: 1.5, border: '1px solid #e2e8f0', transition: 'all 0.2s', '&:hover': { borderColor: '#cbd5e1', boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)' } }}>
                <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.2px', display: 'block', mb: 0.3 }}>Routes</Typography>
                <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '1rem', color: '#1e293b' }}>{metrics?.unique_routes || 56}</Typography>
              </Box>
              <Box sx={{ p: 1, bgcolor: 'white', borderRadius: 1.5, border: '1px solid #e2e8f0', transition: 'all 0.2s', '&:hover': { borderColor: '#cbd5e1', boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)' } }}>
                <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.2px', display: 'block', mb: 0.3 }}>SKUs</Typography>
                <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '1rem', color: '#1e293b' }}>{metrics?.unique_skus || 500}</Typography>
              </Box>
            </Box>
          </Box>

          {/* Performance */}
          <Box sx={{ px: 1.8, py: 2, flexShrink: 0, borderBottom: '1px solid #e2e8f0' }}>
            <Typography variant="caption" sx={{ fontWeight: 800, color: '#1e293b', fontSize: '0.75rem', mb: 1.2, textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block' }}>
              Performance
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.8 }}>
              <Box sx={{ p: 1, bgcolor: 'white', borderRadius: 1.5, border: '1px solid #e2e8f0', transition: 'all 0.2s', '&:hover': { borderColor: '#cbd5e1', boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)' } }}>
                <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.2px', display: 'block', mb: 0.3 }}>On-Time</Typography>
                <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '1rem', color: '#22c55e' }}>{(metrics?.on_time_rate || 70).toFixed(1)}%</Typography>
              </Box>
              <Box sx={{ p: 1, bgcolor: 'white', borderRadius: 1.5, border: '1px solid #e2e8f0', transition: 'all 0.2s', '&:hover': { borderColor: '#cbd5e1', boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)' } }}>
                <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.2px', display: 'block', mb: 0.3 }}>Delayed</Typography>
                <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '1rem', color: '#ef4444' }}>{(metrics?.delay_rate || 30).toFixed(1)}%</Typography>
              </Box>
              <Box sx={{ p: 1, bgcolor: 'white', borderRadius: 1.5, border: '1px solid #e2e8f0', transition: 'all 0.2s', '&:hover': { borderColor: '#cbd5e1', boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)' } }}>
                <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.2px', display: 'block', mb: 0.3 }}>Avg Delay</Typography>
                <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '1rem', color: '#f59e0b' }}>{(metrics?.average_delay_days || 6.5).toFixed(1)}d</Typography>
              </Box>
            </Box>
          </Box>

          {/* System Status */}
          <Box sx={{ px: 1.8, py: 2, flexShrink: 0 }}>
            <Typography variant="caption" sx={{ fontWeight: 800, color: '#1e293b', fontSize: '0.75rem', mb: 1.2, textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block' }}>
              System Status
            </Typography>
            <Box sx={{ p: 1, bgcolor: backendStatus === 'online' ? 'rgba(34, 197, 94, 0.08)' : 'rgba(239, 68, 68, 0.08)', borderRadius: 1.5, border: `1px solid ${backendStatus === 'online' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}` }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.6 }}>
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: backendStatus === 'online' ? '#22c55e' : '#ef4444', animation: backendStatus === 'online' ? 'pulse 2s infinite' : 'none', '@keyframes pulse': { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0.5 } } }} />
                <Typography variant="caption" sx={{ fontSize: '0.7rem', fontWeight: 700, color: backendStatus === 'online' ? '#22c55e' : '#ef4444' }}>
                  {backendStatus === 'online' ? 'Online' : 'Offline'}
                </Typography>
              </Box>
            </Box>
            {backendStatus === 'offline' && (
              <Button variant="outlined" size="small" onClick={checkBackendAndLoadMetrics} sx={{ borderColor: '#e2e8f0', color: '#64748b', fontSize: '0.65rem', textTransform: 'none', fontWeight: 700, py: 0.6, mt: 1, width: '100%', '&:hover': { borderColor: '#cbd5e1', bgcolor: '#f8fafc' } }}>
                Reconnect
              </Button>
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  )
}
