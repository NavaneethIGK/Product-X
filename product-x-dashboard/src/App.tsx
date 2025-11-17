import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Box from '@mui/material/Box'
import Topbar from './components/Topbar'
import Sidebar from './components/Sidebar'
import PredictionsAnalytics from './pages/PredictionsAnalytics'
import AICopilot from './pages/AICopilot'

export default function App() {
  return (
    <Box className="min-h-screen flex">
      <Sidebar />
      <Box className="flex-1">
        <Topbar />
        <Box component="main" className="p-6">
          <Routes>
            <Route path="/" element={<PredictionsAnalytics />} />
            <Route path="/predictions" element={<PredictionsAnalytics />} />
            <Route path="/ai-copilot" element={<AICopilot />} />
            <Route path="*" element={<div>Not Found — <Link to="/">Go home</Link></div>} />
          </Routes>
        </Box>
      </Box>
    </Box>
  )
}
