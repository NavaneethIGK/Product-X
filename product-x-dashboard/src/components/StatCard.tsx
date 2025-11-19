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
        p: 0.9, 
        elevation: 0,
        borderRadius: 2,
        background: bgGradient || '#ffffff',
        color: bgGradient ? 'white' : 'inherit',
        position: 'relative',
        overflow: 'hidden',
        minHeight: 68,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        '&::before': bgGradient ? {
          content: '""',
          position: 'absolute',
          top: 8,
          right: 8,
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.08)',
        } : undefined
      }} 
      elevation={bgGradient ? 4 : 1}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.3 }}>
        <Typography 
          variant="body2" 
          color={bgGradient ? 'inherit' : color} 
          fontWeight={700}
          sx={{ fontSize: '0.78rem' }}
        >
          {title}
        </Typography>
        {icon && <Box sx={{ fontSize: 18, opacity: 0.9 }}>{icon}</Box>}
      </Box>
      <Typography variant="h6" sx={{ fontWeight: 800, mb: 0, fontSize: '1.1rem', lineHeight: 1 }}>
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
