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
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

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
    <Paper sx={{ p: 3 }} elevation={1}>
      <Typography variant="subtitle1" fontWeight={600} mb={2}>
        {title}
      </Typography>
      <Box sx={{ height }}>
        <Line
          data={{ labels, datasets }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true } }
          }}
        />
      </Box>
    </Paper>
  )
}
