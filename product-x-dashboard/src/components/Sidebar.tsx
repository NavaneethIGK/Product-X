import React from 'react'
import { Link as RouterLink } from 'react-router-dom'
import Box from '@mui/material/Box'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'

export default function Sidebar() {
  const menuItems = [
    { label: 'AI Predictions', icon: <AutoAwesomeIcon />, path: '/predictions' },
    { label: 'AI Copilot', icon: <AutoAwesomeIcon />, path: '/ai-copilot' }
  ]

  return (
    <Box component="aside" sx={{ width: 280, borderRight: '1px solid rgba(0,0,0,0.06)', overflowY: 'auto' }} className="hidden md:block">
      <Box sx={{ p: 2, backgroundColor: '#1976d2', color: 'white', fontWeight: 700, fontSize: 18 }}>
        Product X
      </Box>
      <List>
        {menuItems.map((item, idx) => (
          <ListItem key={idx} disablePadding>
            <ListItemButton component={RouterLink} to={item.path} sx={{ py: 1.5 }}>
              <ListItemIcon sx={{ color: '#1976d2' }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  )
}
