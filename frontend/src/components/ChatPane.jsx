import { useState, useRef, useEffect } from 'react'

// Document permission levels (simulated - in production this would come from backend)
const DOCUMENT_PERMISSIONS = {
  'policies/refund-policy.md': 1,      // Public - Employee can see
  'policies/privacy-policy.md': 1,     // Public - Employee can see
  'product/pricing-tiers.md': 1,       // Public - Employee can see
  'faq/general-faq.md': 1,             // Public - Employee can see
  'policies/employee-handbook.md': 2,  // Manager+ only
  'policies/security-guidelines.md': 3, // Admin only
}

function ChatPane({ currentRole = 'employee', roleLevel = 1, onQueryComplete }) {
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState([])
  const [expandedSources, setExpandedSources] = useState({})
  const messagesEndRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Keyboard shortcut: Cmd/Ctrl+Enter to submit
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && query.trim() && !isLoading) {
        e.preventDefault()
        handleSubmit(e)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [query, isLoading])

  const toggleSources = (messageId) => {
    setExpandedSources(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }))
  }

  const formatTime = (isoString) => {
    if (!isoString) return ''
    const date = new Date(isoString)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const formatSourceTime = (isoString) => {
    if (!isoString) return 'unknown'
    const date = new Date(isoString)
    const now = new Date()
    const diffSeconds = Math.floor((now - date) / 1000)

    if (diffSeconds < 60) return 'just now'
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`
    return date.toLocaleDateString()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: query.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setQuery('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.content, top_k: 5, role_level: roleLevel }),
      })
      const data = await response.json()

      // Sources are now filtered on the backend based on role_level
      const filteredSources = data.sources
      const restrictedCount = 0  // Backend handles filtering

      // Track query stats
      if (onQueryComplete) {
        onQueryComplete(Math.round(data.latency_ms))
      }

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: filteredSources.length > 0 ? data.answer : 'No results available for your access level. Try switching to a higher permission role.',
        sources: filteredSources,
        restrictedCount,
        latency: data.latency_ms,
        timestamp: new Date().toISOString(),
      }

      setMessages(prev => [...prev, assistantMessage])
      // Sources are minimized by default - user can expand if needed
    } catch (error) {
      console.error('Query failed:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'Sorry, I encountered an error connecting to the server. Please make sure the backend is running.',
        sources: [],
        latency: 0,
        timestamp: new Date().toISOString(),
        isError: true,
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-b from-gray-50/50 to-white">
      {/* Header */}
      <div className="p-5 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">LiveIndex Chat</h2>
              <p className="text-sm text-gray-500">All your knowledge. Always in sync. Always secure.</p>
            </div>
          </div>
          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg border border-transparent hover:border-red-200 transition-all"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Clear chat
            </button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-center">
            <div className="text-gray-400">
              <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-blue-100 to-blue-200 rounded-2xl flex items-center justify-center">
                <svg className="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <p className="text-lg font-medium text-gray-600">Ask a question</p>
              <p className="text-sm mt-1 text-gray-400">Try: "What is the refund policy?"</p>
              <div className="mt-6 flex flex-wrap gap-2 justify-center max-w-md">
                {['What is the refund policy?', 'How do I reset my password?', 'What browsers are supported?'].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setQuery(suggestion)}
                    className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div key={message.id}>
                {message.type === 'user' ? (
                  // User message
                  <div className="flex justify-end">
                    <div className="max-w-[80%]">
                      <div className="bg-blue-600 text-white px-4 py-2.5 rounded-2xl rounded-br-md shadow-sm">
                        {message.content}
                      </div>
                      <div className="text-xs text-gray-400 mt-1 text-right">
                        {formatTime(message.timestamp)}
                      </div>
                    </div>
                  </div>
                ) : (
                  // Assistant message
                  <div className="flex justify-start">
                    <div className="max-w-[90%]">
                      <div className={`px-4 py-3 rounded-2xl rounded-bl-md shadow-sm ${message.isError ? 'bg-red-50 border border-red-200' : 'bg-gray-100'}`}>
                        <div className="prose prose-sm max-w-none">
                          <p className={`whitespace-pre-wrap text-sm leading-relaxed ${message.isError ? 'text-red-700' : 'text-gray-800'}`}>
                            {message.content}
                          </p>
                        </div>

                        {/* Latency Badge */}
                        {!message.isError && (
                          <div className="mt-3 flex items-center gap-3">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                              </svg>
                              {message.latency?.toFixed(0) || 0}ms
                            </span>
                            {message.sources?.length > 0 && (
                              <button
                                onClick={() => toggleSources(message.id)}
                                className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
                              >
                                <svg className={`w-3 h-3 transition-transform ${expandedSources[message.id] ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                                {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
                              </button>
                            )}
                            {message.restrictedCount > 0 && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-700">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                </svg>
                                {message.restrictedCount} restricted
                              </span>
                            )}
                          </div>
                        )}

                        {/* Collapsible Sources */}
                        {expandedSources[message.id] && message.sources?.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-gray-200">
                            <div className="space-y-2">
                              {message.sources.map((source, index) => (
                                <div
                                  key={index}
                                  className="text-xs bg-white rounded-lg p-3 border border-gray-200 hover:border-blue-200 transition-colors"
                                >
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                      <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                      </svg>
                                      <span className="font-medium text-blue-600">{source.file}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-gray-400">
                                        {formatSourceTime(source.updated_at)}
                                      </span>
                                      <span className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded">
                                        {(source.score * 100).toFixed(0)}%
                                      </span>
                                    </div>
                                  </div>
                                  <p className="text-gray-600 leading-relaxed">{source.chunk}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {formatTime(message.timestamp)}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-md">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                    <span className="text-sm text-gray-500">Searching documents...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything about your knowledge base..."
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-12 transition-shadow"
              disabled={isLoading}
            />
            {query.trim() && !isLoading && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm hover:shadow transition-all"
          >
            {isLoading ? (
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            )}
            Search
          </button>
        </form>
        <p className="text-xs text-gray-400 mt-2 text-center">
          Press Enter to search <span className="text-gray-500">|</span> <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-500 font-mono text-[10px]">⌘</kbd>+<kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-500 font-mono text-[10px]">Enter</kbd> anywhere
        </p>
      </div>
    </div>
  )
}

export default ChatPane
