import React from 'react'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'

type Props = {
  title: string
  value: string
}

export default function Card({ title, value }: Props) {
  return (
    <Paper sx={{ p: 3 }} elevation={1}>
      <Typography variant="subtitle2" color="text.secondary">
        {title}
      </Typography>
      <Box mt={1}>
        <Typography variant="h6">{value}</Typography>
      </Box>
    </Paper>
  )
}
