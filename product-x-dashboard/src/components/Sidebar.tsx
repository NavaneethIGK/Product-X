import React from 'react'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import Box from '@mui/material/Box'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Typography from '@mui/material/Typography'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import SmartToyIcon from '@mui/icons-material/SmartToy'

export default function Sidebar() {
  const location = useLocation()
  
  const menuItems = [
    { label: 'AI Predictions', icon: <TrendingUpIcon />, path: '/predictions' },
    { label: 'AI Copilot', icon: <SmartToyIcon />, path: '/ai-copilot' }
  ]

  const isActive = (path: string) => location.pathname === path || (path === '/predictions' && location.pathname === '/')

  return (
    <Box 
      component="aside" 
      sx={{ 
        width: 280, 
        borderRight: '2px solid #e8eef8',
        overflowY: 'auto',
        backgroundColor: '#ffffff',
        display: { xs: 'none', md: 'flex' },
        flexDirection: 'column',
        height: '100vh'
      }} 
      className="hidden md:block"
    >
      {/* Header */}
      <Box sx={{ 
        p: 3, 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        fontWeight: 800,
        fontSize: 18,
        display: 'flex',
        alignItems: 'center',
        gap: 1.5,
        boxShadow: '0 4px 12px rgba(102, 126, 234, 0.2)'
      }}>
        <Box sx={{ fontSize: 28 }}>📦</Box>
        <Box>
          <Typography sx={{ fontWeight: 800, fontSize: '1.1rem', letterSpacing: 0.5 }}>
            Product X
          </Typography>
          <Typography variant="caption" sx={{ opacity: 0.9, fontSize: '0.75rem' }}>
            Supply Chain
          </Typography>
        </Box>
      </Box>

      {/* Menu */}
      <List sx={{ flex: 1, p: 2 }}>
        {menuItems.map((item, idx) => {
          const active = isActive(item.path)
          return (
            <ListItem key={idx} disablePadding sx={{ mb: 1.5 }}>
              <ListItemButton 
                component={RouterLink} 
                to={item.path}
                sx={{
                  py: 1.8,
                  px: 2.5,
                  borderRadius: '12px',
                  transition: 'all 0.3s ease',
                  backgroundColor: active 
                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                    : 'transparent',
                  color: active ? 'red' : '#667eea',
                  fontWeight: active ? 700 : 600,
                  border: active ? 'none' : '2px solid transparent',
                  boxShadow: active ? '0 6px 20px rgba(102, 126, 234, 0.3)' : 'none',
                  '&:hover': {
                    backgroundColor: active 
                      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                      : 'rgba(102, 126, 234, 0.08)',
                    transform: 'translateX(4px)',
                    boxShadow: active ? '0 6px 20px rgba(102, 126, 234, 0.3)' : 'none'
                  },
                  '& .MuiListItemIcon-root': {
                    color: active ? 'red' : '#667eea',
                    minWidth: 40,
                    transition: 'all 0.3s ease'
                  }
                }}
              >
                <ListItemIcon sx={{ color: 'inherit' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.label}
                  sx={{
                    '& .MuiListItemText-primary': {
                      fontWeight: 'inherit',
                      fontSize: '0.95rem',
                      letterSpacing: 0.3
                    }
                  }}
                />
                {active && (
                  <Box sx={{ 
                    width: 8, 
                    height: 8, 
                    borderRadius: '50%', 
                    backgroundColor: 'white',
                    ml: 1
                  }} />
                )}
              </ListItemButton>
            </ListItem>
          )
        })}
      </List>

      {/* Footer Info */}
      <Box sx={{ 
        p: 2.5, 
        borderTop: '2px solid #e8eef8',
        bgcolor: '#f5f7fb',
        m: 2,
        borderRadius: '12px',
        textAlign: 'center'
      }}>
        <Typography variant="caption" sx={{ color: '#667eea', fontWeight: 700, display: 'block', mb: 1 }}>
          🚀 ACTIVE
        </Typography>
        <Typography variant="caption" sx={{ color: '#1a1a2e', fontWeight: 600, fontSize: '0.85rem' }}>
          1M Shipments
        </Typography>
        <Typography variant="caption" sx={{ color: '#999', display: 'block', fontSize: '0.75rem', mt: 0.5 }}>
          Real-time Analytics
        </Typography>
      </Box>
    </Box>
  )
}
