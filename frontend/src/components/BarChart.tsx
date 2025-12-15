import React from 'react'
import { Bar } from 'react-chartjs-2'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

type Props = {
  title: string
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    backgroundColor: string | string[]
  }>
  height?: number
}

export default function BarChart({ title, labels, datasets, height = 300 }: Props) {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="subtitle1" fontWeight={700} mb={3} sx={{ color: '#333' }}>
        {title}
      </Typography>
      <Box sx={{ height }}>
        <Bar
          data={{ labels, datasets }}
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
                grid: { display: false },
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
