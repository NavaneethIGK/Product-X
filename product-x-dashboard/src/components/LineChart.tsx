import React from 'react'
import { Line } from 'react-chartjs-2'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

type Props = {
  title: string
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    borderColor: string
    backgroundColor?: string
    tension?: number
  }>
  height?: number
}

export default function LineChart({ title, labels, datasets, height = 300 }: Props) {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="subtitle1" fontWeight={700} mb={3} sx={{ color: '#333' }}>
        {title}
      </Typography>
      <Box sx={{ height }}>
        <Line
          data={{ labels, datasets: datasets.map(d => ({ ...d, fill: true, pointRadius: 4, pointBackgroundColor: d.borderColor, pointBorderColor: '#fff', pointBorderWidth: 2 })) }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
              legend: { 
                display: true,
                labels: {
                  padding: 15,
                  font: { size: 12, weight: 500 },
                  usePointStyle: true
                }
              },
              tooltip: {
                backgroundColor: 'rgba(0,0,0,0.8)',
                padding: 12,
                cornerRadius: 6,
                titleFont: { size: 13, weight: 'bold' },
                bodyFont: { size: 12 }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                grid: {
                  color: 'rgba(0,0,0,0.05)',
                  drawBorder: false
                },
                ticks: {
                  font: { size: 11 },
                  color: '#666'
                }
              },
              x: {
                grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false },
                ticks: {
                  font: { size: 11 },
                  color: '#666'
                }
              }
            }
          }}
        />
      </Box>
    </Box>
  )
}
