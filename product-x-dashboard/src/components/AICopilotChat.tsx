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

export default function AICopilotChat({ apiUrl = `http://${window.location.hostname}:8000`, height = 500 }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'assistant',
      content: 'Hello! I\'m your Supply Chain AI Copilot. Ask me about shipment delays, routes, SKUs, or optimization strategies. I\'ll analyze 1M shipments to provide insights.',
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
    <Box sx={{ display: 'flex', flexDirection: 'column', height, bgcolor: '#f5f7fb' }}>
      {/* Header - Premium Gradient */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        p: 3,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        boxShadow: '0 4px 20px rgba(102, 126, 234, 0.3)',
      }}>
        <Box>
          <Typography variant="subtitle1" fontWeight={800} sx={{ fontSize: '1.1rem', letterSpacing: 0.5 }}>
            🤖 AI Supply Chain Copilot
          </Typography>
          <Typography variant="caption" sx={{ opacity: 0.95, display: 'block', mt: 0.5, fontWeight: 500 }}>
            Analyzing 1M shipments • Real-time insights
          </Typography>
        </Box>
        <IconButton 
          size="small" 
          onClick={handleClear} 
          title="Clear chat" 
          sx={{ 
            color: 'white',
            '&:hover': {
              backgroundColor: 'rgba(255,255,255,0.2)'
            }
          }}
        >
          <DeleteIcon fontSize="small" />
        </IconButton>
      </Box>

      {/* Messages Container */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 2.5,
          p: 3,
          bgcolor: '#f5f7fb',
          '&::-webkit-scrollbar': {
            width: '10px'
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: '#e8eef8',
            borderRadius: 4
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: '#b0bae0',
            borderRadius: 4,
            '&:hover': {
              backgroundColor: '#8b95ca'
            }
          }
        }}
      >
        {messages.map((msg) => (
          <Box
            key={msg.id}
            sx={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              animation: 'fadeIn 0.3s ease-in',
              '@keyframes fadeIn': {
                from: { opacity: 0, transform: 'translateY(10px)' },
                to: { opacity: 1, transform: 'translateY(0)' }
              }
            }}
          >
            <Paper
              sx={{
                p: 3,
                maxWidth: '80%',
                backgroundColor: msg.role === 'user' 
                  ? '#667eea' 
                  : '#ffffff',
                color: msg.role === 'user' ? '#ffffff' : '#1a1a2e',
                borderRadius: msg.role === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                boxShadow: msg.role === 'user' 
                  ? '0 6px 20px rgba(102, 126, 234, 0.4)' 
                  : '0 4px 12px rgba(0,0,0,0.08)',
                border: msg.role === 'assistant' ? '1px solid #e8eef8' : 'none',
                backdropFilter: msg.role === 'user' ? 'blur(10px)' : 'none'
              }}
              elevation={0}
            >
              <Box sx={{ 
                '& p': { 
                  margin: 0, 
                  lineHeight: 1.7,
                  fontSize: '0.96rem',
                  fontWeight: 500
                }, 
                '& strong': {
                  fontWeight: 800,
                  color: msg.role === 'user' ? '#ffffff' : '#667eea'
                },
                '& code': { 
                  bgcolor: msg.role === 'user' ? 'rgba(255,255,255,0.2)' : '#f0f2fb',
                  color: msg.role === 'user' ? '#ffffff' : '#667eea',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  fontFamily: '"Fira Code", "Monaco", monospace',
                  fontSize: '0.85em',
                  fontWeight: 700,
                  border: msg.role === 'user' ? '1px solid rgba(255,255,255,0.3)' : '1px solid rgba(102, 126, 234, 0.2)'
                },
                '& ul, & ol': {
                  paddingLeft: '20px',
                  margin: '12px 0'
                },
                '& li': {
                  marginBottom: '8px'
                },
                '& h3, & h4, & h5': {
                  margin: '12px 0 8px 0',
                  color: msg.role === 'user' ? '#ffffff' : '#667eea',
                  fontWeight: 700
                }
              }}>
                <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                  <Markdown>{msg.content}</Markdown>
                </Typography>
              </Box>
            </Paper>
          </Box>
        ))}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', gap: 1.5, alignItems: 'center' }}>
            <CircularProgress size={28} sx={{ color: '#667eea' }} thickness={5} />
            <Typography variant="caption" color="#667eea" sx={{ fontWeight: 600, fontSize: '0.9rem' }}>
              Analyzing data...
            </Typography>
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Suggested Queries */}
      {messages.length <= 2 && (
        <Box sx={{ px: 3, pb: 2, bgcolor: '#f5f7fb' }}>
          <Typography variant="caption" sx={{ color: '#667eea', display: 'block', mb: 1.5, fontWeight: 700, fontSize: '0.85rem', letterSpacing: 0.5 }}>
            💡 TRY ASKING
          </Typography>
          <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
            {suggestedQueries.map((query, idx) => (
              <Chip
                key={idx}
                label={query}
                onClick={() => setInput(query)}
                size="small"
                variant="outlined"
                sx={{
                  borderColor: '#667eea',
                  color: '#667eea',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  borderRadius: '20px',
                  backgroundColor: '#ffffff',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    backgroundColor: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: '#ffffff',
                    borderColor: '#764ba2',
                    boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
                    transform: 'translateY(-2px)'
                  },
                  cursor: 'pointer'
                }}
              />
            ))}
          </Box>
        </Box>
      )}

      {/* Input Area - Premium Design */}
      <Box sx={{ 
        display: 'flex', 
        gap: 1.5,
        p: 2.5,
        borderTop: '2px solid #e8eef8',
        bgcolor: '#ffffff',
        boxShadow: '0 -4px 12px rgba(0,0,0,0.05)'
      }}>
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
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: '12px',
              backgroundColor: '#f5f7fb',
              fontSize: '0.95rem',
              fontWeight: 500,
              border: '2px solid #e8eef8',
              transition: 'all 0.3s ease',
              '&:hover fieldset': {
                borderColor: '#667eea'
              },
              '&.Mui-focused': {
                backgroundColor: '#ffffff',
                '& fieldset': {
                  borderColor: '#667eea',
                  borderWidth: 2
                }
              },
              '&.Mui-disabled': {
                backgroundColor: '#f5f7fb',
                opacity: 0.6
              }
            },
            '& .MuiOutlinedInput-input::placeholder': {
              opacity: 0.6,
              fontWeight: 500
            }
          }}
        />
        <IconButton
          color="primary"
          onClick={handleSendMessage}
          disabled={!input.trim() || loading}
          title="Send message (Enter)"
          sx={{
            background: !input.trim() || loading 
              ? 'rgba(102, 126, 234, 0.4)' 
              : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            borderRadius: '12px',
            padding: '12px',
            minWidth: '48px',
            transition: 'all 0.3s ease',
            boxShadow: !input.trim() || loading 
              ? 'none'
              : '0 4px 15px rgba(102, 126, 234, 0.3)',
            '&:hover:not(:disabled)': {
              boxShadow: '0 6px 25px rgba(102, 126, 234, 0.4)',
              transform: 'translateY(-2px)'
            },
            '&:active:not(:disabled)': {
              transform: 'translateY(0)'
            }
          }}
        >
          <SendIcon sx={{ fontSize: '1.3rem' }} />
        </IconButton>
      </Box>
    </Box>
  )
}
