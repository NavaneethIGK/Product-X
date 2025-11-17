import React, { useState, useEffect } from 'react'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'
import Grid from '@mui/material/Grid'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Chip from '@mui/material/Chip'
import Button from '@mui/material/Button'
import FilterBar from '../components/FilterBar'
import StatCard from '../components/StatCard'
import DataTable from '../components/DataTable'
import { getShipmentData } from '../utils/storage'

export default function ShipmentDetails() {
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [data, setData] = useState(getShipmentData())

  useEffect(() => {
    const storedData = getShipmentData()
    setData(storedData)
  }, [])

  const handleFilterChange = (newFilters: Record<string, string>) => {
    setFilters(newFilters)
  }

  const handleRefresh = () => {
    const storedData = getShipmentData()
    setData(storedData)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Delivered':
        return 'success'
      case 'In Transit':
        return 'info'
      case 'Delayed':
        return 'warning'
      case 'Cancelled':
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
          Shipment Details & History
        </Typography>
        <Button variant="outlined" size="small" onClick={handleRefresh}>
          Refresh Data
        </Button>
      </Box>

      <FilterBar
        filters={[
          {
            key: 'shipmentId',
            label: 'Shipment ID',
            type: 'text'
          },
          {
            key: 'status',
            label: 'Status',
            type: 'select',
            options: [
              { label: 'Delivered', value: 'delivered' },
              { label: 'In Transit', value: 'transit' },
              { label: 'Delayed', value: 'delayed' },
              { label: 'Cancelled', value: 'cancelled' }
            ]
          },
          {
            key: 'warehouse',
            label: 'Origin',
            type: 'select',
            options: [
              { label: 'Warehouse 1', value: '1' },
              { label: 'Warehouse 2', value: '2' },
              { label: 'Warehouse 3', value: '3' }
            ]
          }
        ]}
        onFilterChange={handleFilterChange}
      />

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Total Shipments" value={data.totalShipments} color="primary.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Delivered" value={data.delivered} color="success.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="In Transit" value={data.inTransit} color="info.main" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Delayed" value={data.delayed} color="warning.main" />
        </Grid>
      </Grid>

      {/* Detailed Shipment View */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }} elevation={1}>
            <Typography variant="subtitle1" fontWeight={600} mb={3}>
              Recent Shipments
            </Typography>
            <Box>
              {data.shipments.slice(0, 3).map((shipment) => (
                <Paper
                  key={shipment.shipmentId}
                  sx={{
                    p: 3,
                    mb: 2,
                    border: '1px solid #e0e0e0',
                    '&:hover': { boxShadow: 2 }
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        {shipment.shipmentId}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {shipment.supplier} → {shipment.destination}
                      </Typography>
                    </Box>
                    <Chip
                      label={shipment.status}
                      color={getStatusColor(shipment.status) as any}
                      variant="outlined"
                      size="small"
                    />
                  </Box>

                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Supplier
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {shipment.supplier}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Destination
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {shipment.destination}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          ETA
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {shipment.eta}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Progress
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {shipment.progress}
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </Paper>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Comprehensive Table */}
      <Box sx={{ mt: 4 }}>
        <DataTable
          title="All Shipments"
          columns={[
            { key: 'shipmentId', label: 'Shipment ID' },
            { key: 'supplier', label: 'Supplier' },
            { key: 'destination', label: 'Destination' },
            { key: 'eta', label: 'ETA' },
            { key: 'status', label: 'Status' },
            { key: 'progress', label: 'Progress' }
          ]}
          rows={data.shipments}
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
