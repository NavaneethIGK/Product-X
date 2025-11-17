import React, { useState, useEffect } from 'react'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'
import Grid from '@mui/material/Grid'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import FilterBar from '../components/FilterBar'
import StatCard from '../components/StatCard'
import DataTable from '../components/DataTable'
import { getInventoryData } from '../utils/storage'

export default function InventoryManagement() {
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [data, setData] = useState(getInventoryData())

  useEffect(() => {
    const storedData = getInventoryData()
    setData(storedData)
  }, [])

  const handleFilterChange = (newFilters: Record<string, string>) => {
    setFilters(newFilters)
  }

  const handleRefresh = () => {
    const storedData = getInventoryData()
    setData(storedData)
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
          Inventory Management
        </Typography>
        <Button variant="outlined" size="small" onClick={handleRefresh}>
          Refresh Data
        </Button>
      </Box>

      <FilterBar
        filters={[
          {
            key: 'warehouse',
            label: 'Warehouse',
            type: 'select',
            options: [
              { label: 'Warehouse 1', value: '1' },
              { label: 'Warehouse 2', value: '2' },
              { label: 'Warehouse 3', value: '3' },
              { label: 'Warehouse 4', value: '4' },
              { label: 'Warehouse 5', value: '5' }
            ]
          },
          {
            key: 'date',
            label: 'Date Range',
            type: 'text'
          }
        ]}
        onFilterChange={handleFilterChange}
      />

      {/* Inventory Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Box sx={{ p: 3, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Stock Levels
            </Typography>
            <Box sx={{ display: 'flex', gap: 4 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Out of Stock
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#e53935' }}>
                  {data.outOfStock}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  In Stock
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#4caf50' }}>
                  {data.inStock}
                </Typography>
              </Box>
            </Box>
          </Box>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Box sx={{ p: 3, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Returns
            </Typography>
            <Box sx={{ display: 'flex', gap: 4 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Returned Units
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {data.returnedUnits.toLocaleString()}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Ordered Units
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {data.orderedUnits.toLocaleString()}
                </Typography>
              </Box>
            </Box>
          </Box>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Box sx={{ p: 3, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Backorder Status
            </Typography>
            <Box sx={{ display: 'flex', gap: 4 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Backorders
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {data.backorders}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Total Orders
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {data.totalOrders}
                </Typography>
              </Box>
            </Box>
          </Box>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Return Rate"
            value={((data.returnedUnits / data.orderedUnits) * 100).toFixed(2) + '%'}
            color="warning.main"
          />
        </Grid>
      </Grid>

      {/* Warehouse Summary Table */}
      <Box sx={{ mt: 4 }}>
        <DataTable
          title="Inventory Summary by Warehouse"
          columns={[
            { key: 'warehouse', label: 'Warehouse' },
            { key: 'items', label: 'Total Items' },
            { key: 'value', label: 'Inventory Value' },
            { key: 'turnover', label: 'Turnover Ratio' },
            { key: 'days', label: 'Days of Supply' }
          ]}
          rows={data.warehouseStats}
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
