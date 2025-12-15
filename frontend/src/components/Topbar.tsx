import React from 'react'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'

export default function Topbar() {
  return (
    <AppBar 
      position="static" 
      color="transparent" 
      elevation={0} 
      sx={{ 
        borderBottom: '2px solid #e8eef8',
        bgcolor: '#ffffff',
        backdropFilter: 'blur(8px)',
        background: 'rgba(255, 255, 255, 0.95)'
      }}
    >
      <Toolbar sx={{ py: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{
            width: 40,
            height: 40,
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.5rem'
          }}>
            📦
          </Box>
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ 
              fontWeight: 800,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontSize: '1.3rem',
              letterSpacing: 0.5
            }}
          >
            Product X
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        <Box sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          px: 2,
          py: 1,
          borderRadius: '8px',
          bgcolor: '#f5f7fb',
          color: '#667eea',
          fontWeight: 600,
          fontSize: '0.85rem'
        }}>
          🚀 Supply Chain Intelligence
        </Box>
      </Toolbar>
    </AppBar>
  )
}
