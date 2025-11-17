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
  bgGradient?: string
  icon?: React.ReactNode
}

export default function StatCard({ 
  title, 
  value, 
  subtitle, 
  color = 'text.secondary',
  bgGradient,
  icon 
}: Props) {
  return (
    <Paper 
      sx={{ 
        p: 3, 
        elevation: 0,
        borderRadius: 2,
        background: bgGradient || '#ffffff',
        color: bgGradient ? 'white' : 'inherit',
        position: 'relative',
        overflow: 'hidden',
        '&::before': bgGradient ? {
          content: '""',
          position: 'absolute',
          top: 0,
          right: 0,
          width: 100,
          height: 100,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.1)',
        } : undefined
      }} 
      elevation={bgGradient ? 4 : 1}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
        <Typography 
          variant="body2" 
          color={bgGradient ? 'inherit' : color} 
          fontWeight={600} 
        >
          {title}
        </Typography>
        {icon && <Box sx={{ fontSize: 28, opacity: 0.8 }}>{icon}</Box>}
      </Box>
      <Typography variant="h4" sx={{ fontWeight: 800, mb: 1 }}>
        {value}
      </Typography>
      {subtitle && (
        <Typography 
          variant="caption" 
          color={bgGradient ? 'rgba(255,255,255,0.8)' : 'text.secondary'} 
          display="block" 
          mt={0.5}
          sx={{ fontSize: '0.8rem' }}
        >
          {subtitle}
        </Typography>
      )}
    </Paper>
  )
}
