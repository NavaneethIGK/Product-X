import React from 'react'
import { Doughnut } from 'react-chartjs-2'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

type Props = {
  title: string
  labels: string[]
  data: number[]
  backgroundColor: string[]
  height?: number
}

export default function PieChart({ title, labels, data, backgroundColor, height = 300 }: Props) {
  return (
    <Paper sx={{ p: 3 }} elevation={1}>
      <Typography variant="subtitle1" fontWeight={600} mb={2}>
        {title}
      </Typography>
      <Box sx={{ height }}>
        <Doughnut
          data={{ labels, datasets: [{ data, backgroundColor, borderWidth: 2 }] }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'right' as const } }
          }}
        />
      </Box>
    </Paper>
  )
}
