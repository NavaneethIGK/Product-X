import React, { useState, useRef, useEffect } from 'react'
import Paper from '@mui/material/Paper'
import TextField from '@mui/material/TextField'
import IconButton from '@mui/material/IconButton'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import Chip from '@mui/material/Chip'
import SendIcon from '@mui/icons-material/Send'
import DeleteIcon from '@mui/icons-material/Delete'
import Markdown from 'react-markdown'

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

type Props = {
  apiUrl?: string
  height?: number
}

export default function AICopilotChat({ apiUrl = 'http://localhost:8000', height = 500 }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'assistant',
      content: 'Hello! I\'m your Supply Chain AI Copilot. Ask me about shipment delays, routes, SKUs, or optimization strategies.',
      timestamp: new Date().toISOString()
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!input.trim()) return

    const userQuery = input
    const userMessage: Message = {
      id: Math.random().toString(),
      role: 'user',
      content: userQuery,
      timestamp: new Date().toISOString()
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage].map((m) => ({ role: m.role, content: m.content })),
          query: userQuery
        })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: Math.random().toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString()
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: Math.random().toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Make sure the backend server is running at ' + apiUrl,
        timestamp: new Date().toISOString()
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setMessages([
      {
        id: '0',
        role: 'assistant',
        content: 'Chat cleared. Ask me anything about your supply chain!',
        timestamp: new Date().toISOString()
      }
    ])
  }

  const suggestedQueries = [
    'What routes have the most delays?',
    'Which SKUs are problematic?',
    'How can we reduce delays?',
    'What is our on-time delivery rate?'
  ]

  return (
    <Paper sx={{ display: 'flex', flexDirection: 'column', height, p: 2 }} elevation={1}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          🤖 AI Supply Chain Copilot
        </Typography>
        <IconButton size="small" onClick={handleClear} title="Clear chat">
          <DeleteIcon fontSize="small" />
        </IconButton>
      </Box>

      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          mb: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          pr: 1,
          '&::-webkit-scrollbar': {
            width: '6px'
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: '#f1f1f1',
            borderRadius: 3
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: '#888',
            borderRadius: 3,
            '&:hover': {
              backgroundColor: '#555'
            }
          }
        }}
      >
        {messages.map((msg) => (
          <Box
            key={msg.id}
            sx={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <Paper
              sx={{
                p: 1.5,
                maxWidth: '85%',
                backgroundColor: msg.role === 'user' ? '#1976d2' : '#f5f5f5',
                color: msg.role === 'user' ? 'white' : '#333'
              }}
              elevation={0}
            >
              <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                <Markdown>{msg.content}</Markdown>
              </Typography>
            </Paper>
          </Box>
        ))}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
            <CircularProgress size={24} />
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Suggested Queries (shown when few messages) */}
      {messages.length <= 2 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary" display="block" mb={1}>
            Try asking:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {suggestedQueries.map((query, idx) => (
              <Chip
                key={idx}
                label={query}
                onClick={() => {
                  setInput(query)
                }}
                size="small"
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      )}

      {/* Input */}
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Ask about delays, routes, SKUs, or optimization..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSendMessage()
            }
          }}
          disabled={loading}
        />
        <IconButton
          color="primary"
          onClick={handleSendMessage}
          disabled={!input.trim() || loading}
          title="Send message"
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Paper>
  )
}
