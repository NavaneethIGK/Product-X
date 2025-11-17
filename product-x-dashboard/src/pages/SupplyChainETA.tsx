import React, { useState, useEffect } from 'react'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'
import Grid from '@mui/material/Grid'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Button from '@mui/material/Button'
import FilterBar from '../components/FilterBar'
import StatCard from '../components/StatCard'
import LineChart from '../components/LineChart'
import DataTable from '../components/DataTable'
import { getETAData } from '../utils/storage'

export default function SupplyChainETA() {
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [data, setData] = useState(getETAData())

  useEffect(() => {
    const storedData = getETAData()
    setData(storedData)
  }, [])

  const handleFilterChange = (newFilters: Record<string, string>) => {
    setFilters(newFilters)
  }

  const handleRefresh = () => {
    const storedData = getETAData()
    setData(storedData)
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
          Supply Chain ETA & Delivery Tracking
        </Typography>
        <Button variant="outlined" size="small" onClick={handleRefresh}>
          Refresh Data
        </Button>
      </Box>

      <FilterBar
        filters={[
          {
            key: 'supplier',
            label: 'Supplier',
            type: 'select',
            options: [
              { label: 'Supplier A', value: 'A' },
              { label: 'Supplier B', value: 'B' },
              { label: 'Supplier C', value: 'C' },
              { label: 'Supplier D', value: 'D' }
            ]
          },
          {
            key: 'status',
            label: 'Status',
            type: 'select',
            options: [
              { label: 'In Transit', value: 'transit' },
              { label: 'Delayed', value: 'delayed' },
              { label: 'On Time', value: 'ontime' },
              { label: 'Delivered', value: 'delivered' }
            ]
          }
        ]}
        onFilterChange={handleFilterChange}
      />

      {/* Top Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="On-Time Delivery" value={`${data.onTimeDelivery}%`} color="success.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Average ETA" value={`${data.avgEta} days`} color="info.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Delayed Shipments" value={data.delayedShipments} color="warning.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="In Transit" value={data.inTransit} color="secondary.main" />
        </Grid>
      </Grid>

      {/* ETA Timeline */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }} elevation={1}>
            <Typography variant="subtitle1" fontWeight={600} mb={2}>
              Shipment ETA by Destination
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 2, overflowX: 'auto', pb: 1 }}>
              {[
                { dest: 'New York', eta: '2023-09-25', status: 'On Time' },
                { dest: 'Los Angeles', eta: '2023-09-26', status: 'Delayed' },
                { dest: 'Chicago', eta: '2023-09-24', status: 'On Time' },
                { dest: 'Houston', eta: '2023-09-27', status: 'In Transit' },
                { dest: 'Phoenix', eta: '2023-09-28', status: 'Delayed' }
              ].map((item) => (
                <Box
                  key={item.dest}
                  sx={{
                    minWidth: 150,
                    p: 2,
                    border: '1px solid #e0e0e0',
                    borderRadius: 1,
                    textAlign: 'center'
                  }}
                >
                  <Typography variant="body2" fontWeight={600}>
                    {item.dest}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ETA: {item.eta}
                  </Typography>
                  <Box
                    sx={{
                      mt: 1,
                      p: 0.5,
                      borderRadius: 0.5,
                      backgroundColor:
                        item.status === 'On Time'
                          ? '#c8e6c9'
                          : item.status === 'Delayed'
                            ? '#ffccbc'
                            : '#b3e5fc',
                      color:
                        item.status === 'On Time'
                          ? '#2e7d32'
                          : item.status === 'Delayed'
                            ? '#d84315'
                            : '#0277bd'
                    }}
                  >
                    <Typography variant="caption" fontWeight={600}>
                      {item.status}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* ETA Forecast Chart */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <LineChart
            title="Shipment Arrivals Forecast (Next 30 Days)"
            labels={data.etaForecast.map((d) => d.date)}
            datasets={[
              {
                label: 'Expected Arrivals',
                data: data.etaForecast.map((d) => d.arrivals),
                borderColor: '#2196f3',
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                tension: 0.4
              }
            ]}
            height={350}
          />
        </Grid>
      </Grid>

      {/* Shipment Details Table */}
      <Box sx={{ mt: 4 }}>
        <DataTable
          title="Active Shipments"
          columns={[
            { key: 'shipmentId', label: 'Shipment ID' },
            { key: 'supplier', label: 'Supplier' },
            { key: 'destination', label: 'Destination' },
            { key: 'eta', label: 'ETA' },
            { key: 'status', label: 'Status' },
            { key: 'progress', label: 'Progress' }
          ]}
          rows={data.activeShipments}
        />
      </Box>

      <Box sx={{ mt: 2 }}>
        <Typography variant="caption" color="text.secondary">
          Data loaded from localStorage • Last updated: {new Date().toLocaleString()}
        </Typography>
      </Box>
    </Container>
  )
}
