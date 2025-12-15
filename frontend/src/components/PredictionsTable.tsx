import React, { useState, useEffect } from 'react'
import Paper from '@mui/material/Paper'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'

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

type Props = {
  predictions?: Prediction[]
  maxRows?: number
}

export default function PredictionsTable({ predictions = [], maxRows = 20 }: Props) {
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'HIGH':
        return 'error'
      case 'MEDIUM':
        return 'warning'
      case 'LOW':
        return 'success'
      default:
        return 'default'
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <Paper sx={{ p: 3 }} elevation={1}>
      <Typography variant="subtitle1" fontWeight={600} mb={2}>
        ETA Predictions (AI Model)
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600 }}>Shipment ID</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Route</TableCell>
              <TableCell align="center" sx={{ fontWeight: 600 }}>
                Predicted Days
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 600 }}>
                Predicted Arrival
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 600 }}>
                Confidence
              </TableCell>
              <TableCell align="center" sx={{ fontWeight: 600 }}>
                Delay Risk
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {predictions.slice(0, maxRows).map((pred) => (
              <TableRow key={pred.shipment_id} hover>
                <TableCell sx={{ fontWeight: 500 }}>{pred.shipment_id}</TableCell>
                <TableCell>{pred.route}</TableCell>
                <TableCell align="center">{pred.predicted_days} days</TableCell>
                <TableCell align="center">{formatDate(pred.predicted_arrival)}</TableCell>
                <TableCell align="center">
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        width: 60,
                        height: 6,
                        backgroundColor: '#e0e0e0',
                        borderRadius: 1,
                        overflow: 'hidden'
                      }}
                    >
                      <Box
                        sx={{
                          width: `${pred.confidence}%`,
                          height: '100%',
                          backgroundColor: pred.confidence > 80 ? '#4caf50' : pred.confidence > 70 ? '#ff9800' : '#f44336'
                        }}
                      />
                    </Box>
                    <Typography variant="caption" sx={{ minWidth: 35 }}>
                      {pred.confidence}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={pred.delay_risk}
                    color={getRiskColor(pred.delay_risk) as any}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Typography variant="caption" color="text.secondary" display="block" mt={2}>
        Showing {Math.min(maxRows, predictions.length)} of {predictions.length} predictions
      </Typography>
    </Paper>
  )
}
