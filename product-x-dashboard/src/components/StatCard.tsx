import React from 'react'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import Grid from '@mui/material/Grid'

type Props = {
  title: string
  value: string | number
  subtitle?: string
  color?: string
}

export default function StatCard({ title, value, subtitle, color = 'text.secondary' }: Props) {
  return (
    <Paper sx={{ p: 2 }} elevation={1}>
      <Typography variant="body2" color={color} fontWeight={600} mb={1}>
        {title}
      </Typography>
      <Typography variant="h5" sx={{ fontWeight: 700 }}>
        {value}
      </Typography>
      {subtitle && (
        <Typography variant="caption" color="text.secondary" display="block" mt={0.5}>
          {subtitle}
        </Typography>
      )}
    </Paper>
  )
}
