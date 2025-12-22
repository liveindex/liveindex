import { useState, useEffect, useCallback } from 'react'
import DocumentPane from './components/DocumentPane'
import ChatPane from './components/ChatPane'
import SyncNotification from './components/SyncNotification'
import useWebSocket from './hooks/useWebSocket'

// Role definitions with permissions
const ROLES = {
  employee: { label: 'Employee', color: 'gray', icon: 'user', level: 1 },
  manager: { label: 'Manager', color: 'blue', icon: 'briefcase', level: 2 },
  admin: { label: 'Admin', color: 'purple', icon: 'shield', level: 3 },
}

function App() {
  const [documents, setDocuments] = useState([])
  const [status, setStatus] = useState({
    documentsIndexed: 0,
    watcherActive: false,
    lastSync: null,
  })
  const [notifications, setNotifications] = useState([])
  const [recentlyUpdated, setRecentlyUpdated] = useState([])
  const [updateBanner, setUpdateBanner] = useState(null)
  const [currentRole, setCurrentRole] = useState('employee')
  const [showRoleMenu, setShowRoleMenu] = useState(false)
  const [queryStats, setQueryStats] = useState({ totalQueries: 0, avgLatency: 0, lastQueries: [] })

  // WebSocket connection for real-time updates
  const { lastMessage, isConnected } = useWebSocket('ws://localhost:8000/ws')

  // Fetch documents from API
  const fetchDocuments = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/documents')
      const data = await response.json()
      setDocuments(data.documents || [])

      // Also fetch status
      const statusResponse = await fetch('http://localhost:8000/status')
      const statusData = await statusResponse.json()
      setStatus({
        documentsIndexed: statusData.documents_indexed || 0,
        watcherActive: statusData.watcher_active || false,
        lastSync: statusData.last_sync,
      })
    } catch (error) {
      console.error('Failed to fetch documents:', error)
    }
  }, [])

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return

    const { event } = lastMessage

    if (event === 'connected') {
      // Initial state from server
      const { status: serverStatus } = lastMessage
      setDocuments(serverStatus.documents || [])
      setStatus({
        documentsIndexed: serverStatus.documents_indexed || 0,
        watcherActive: serverStatus.watcher_active || false,
        lastSync: serverStatus.last_sync,
      })
    } else if (event === 'document_updated') {
      // Show notification for document update
      addNotification({
        type: 'update',
        file: lastMessage.file,
        message: `Detected change: ${lastMessage.file}`,
      })
    } else if (event === 'reindex_complete') {
      // Add to recently updated list
      setRecentlyUpdated(prev => {
        const updated = [lastMessage.file, ...prev.filter(f => f !== lastMessage.file)]
        return updated.slice(0, 10) // Keep last 10
      })

      // Show notification for reindex completion
      addNotification({
        type: 'success',
        file: lastMessage.file,
        message: `Reindexed ${lastMessage.file} in ${lastMessage.time_ms.toFixed(0)}ms`,
      })

      // Show prominent update banner
      setUpdateBanner({
        file: lastMessage.file,
        time_ms: lastMessage.time_ms,
      })
      setTimeout(() => setUpdateBanner(null), 4000)

      // Update last sync time
      setStatus(prev => ({
        ...prev,
        lastSync: lastMessage.timestamp,
      }))

      // Refresh document list
      fetchDocuments()

      // Clear from recently updated after 10 seconds
      setTimeout(() => {
        setRecentlyUpdated(prev => prev.filter(f => f !== lastMessage.file))
      }, 10000)
    }
  }, [lastMessage, fetchDocuments])

  // Add notification with auto-dismiss
  const addNotification = (notification) => {
    const id = Date.now()
    setNotifications(prev => [...prev, { ...notification, id }])
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id))
    }, 5000)
  }

  // Initial fetch
  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  // Track query stats
  const trackQuery = (latency) => {
    setQueryStats(prev => {
      const newQueries = [{ latency, time: Date.now() }, ...prev.lastQueries].slice(0, 20)
      const avgLatency = newQueries.reduce((sum, q) => sum + q.latency, 0) / newQueries.length
      return {
        totalQueries: prev.totalQueries + 1,
        avgLatency: Math.round(avgLatency),
        lastQueries: newQueries,
      }
    })
  }

  // Get role icon
  const getRoleIcon = (role) => {
    switch (role) {
      case 'employee':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        )
      case 'manager':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        )
      case 'admin':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        )
      default:
        return null
    }
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center gap-4">
            <div className="w-11 h-11 bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 tracking-tight">LiveIndex</h1>
              <p className="text-xs text-gray-500 font-medium">Real-time knowledge infrastructure for AI</p>
            </div>
          </div>

          {/* Status Buttons & Stats */}
          <div className="flex items-center gap-3">
            {/* Role Selector */}
            <div className="relative">
              <button
                onClick={() => setShowRoleMenu(!showRoleMenu)}
                className={`
                  flex items-center gap-2.5 px-4 py-2 rounded-lg font-medium text-sm transition-all border shadow-sm
                  ${currentRole === 'admin' ? 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100' :
                    currentRole === 'manager' ? 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100' :
                    'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'}
                `}
              >
                {getRoleIcon(currentRole)}
                <span>{ROLES[currentRole].label}</span>
                <svg className={`w-4 h-4 transition-transform ${showRoleMenu ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown Menu */}
              {showRoleMenu && (
                <div className="absolute top-full right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-gray-200 py-2 z-50">
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Switch Role</p>
                  </div>
                  {Object.entries(ROLES).map(([key, role]) => (
                    <button
                      key={key}
                      onClick={() => {
                        setCurrentRole(key)
                        setShowRoleMenu(false)
                        addNotification({
                          type: 'success',
                          message: `Switched to ${role.label} role`,
                        })
                      }}
                      className={`
                        w-full flex items-center gap-3 px-4 py-2.5 text-left transition-all
                        ${currentRole === key ? 'bg-gray-50' : 'hover:bg-gray-50'}
                      `}
                    >
                      <div className={`
                        w-8 h-8 rounded-lg flex items-center justify-center
                        ${key === 'admin' ? 'bg-purple-100 text-purple-600' :
                          key === 'manager' ? 'bg-blue-100 text-blue-600' :
                          'bg-gray-100 text-gray-600'}
                      `}>
                        {getRoleIcon(key)}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{role.label}</div>
                        <div className="text-xs text-gray-500">
                          {key === 'admin' ? 'Full access to all documents' :
                           key === 'manager' ? 'Access to team & public docs' :
                           'Access to public documents only'}
                        </div>
                      </div>
                      {currentRole === key && (
                        <svg className="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Divider */}
            <div className="h-8 w-px bg-gray-200" />

            {/* Watcher Status Button */}
            <button className={`
              flex items-center gap-2.5 px-4 py-2 rounded-lg font-medium text-sm transition-all
              ${status.watcherActive
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm hover:bg-emerald-100'
                : 'bg-gray-100 text-gray-500 border border-gray-200 hover:bg-gray-150'}
            `}>
              <div className="relative flex items-center justify-center">
                <span className={`w-2.5 h-2.5 rounded-full ${status.watcherActive ? 'bg-emerald-500' : 'bg-gray-400'}`} />
                {status.watcherActive && (
                  <span className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping opacity-50" />
                )}
              </div>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <span>{status.watcherActive ? 'Watching' : 'Inactive'}</span>
            </button>

            {/* Connection Status Button */}
            <button className={`
              flex items-center gap-2.5 px-4 py-2 rounded-lg font-medium text-sm transition-all
              ${isConnected
                ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-sm hover:bg-blue-100'
                : 'bg-red-50 text-red-600 border border-red-200 hover:bg-red-100'}
            `}>
              <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-blue-500' : 'bg-red-500'}`} />
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>{isConnected ? 'Live' : 'Offline'}</span>
            </button>

            {/* Divider */}
            <div className="h-8 w-px bg-gray-200 mx-1" />

            {/* Stats Cards */}
            <div className="flex items-center gap-2">
              {/* Files Card */}
              <div className="flex items-center gap-2.5 px-4 py-2 bg-gradient-to-br from-violet-50 to-purple-50 border border-violet-200 rounded-lg shadow-sm">
                <div className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-violet-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <div className="text-lg font-bold text-violet-700">{documents.length}</div>
                  <div className="text-xs text-violet-500 font-medium -mt-0.5">Files</div>
                </div>
              </div>

              {/* Chunks Card */}
              <div className="flex items-center gap-2.5 px-4 py-2 bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-lg shadow-sm">
                <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div>
                  <div className="text-lg font-bold text-amber-700">{status.documentsIndexed}</div>
                  <div className="text-xs text-amber-500 font-medium -mt-0.5">Chunks</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Update Banner - Shows prominently when document is reindexed */}
      {updateBanner && (
        <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-6 py-3 flex items-center justify-center gap-3 animate-pulse shadow-lg">
          <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold">Document Updated!</span>
            <span className="opacity-90">{updateBanner.file}</span>
            <span className="px-2 py-0.5 bg-white/20 rounded-full text-sm">
              {updateBanner.time_ms.toFixed(0)}ms
            </span>
          </div>
          <span className="text-sm opacity-75">Re-query to see updated results</span>
        </div>
      )}

      {/* Main Content - Split Pane */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Pane - Documents */}
        <div className="w-80 min-w-80 border-r border-gray-200 bg-white overflow-hidden flex flex-col">
          <DocumentPane
            documents={documents}
            status={status}
            onRefresh={fetchDocuments}
            recentlyUpdated={recentlyUpdated}
          />
        </div>

        {/* Right Pane - Chat */}
        <div className="flex-1 bg-white overflow-hidden flex flex-col">
          <ChatPane
            currentRole={currentRole}
            roleLevel={ROLES[currentRole].level}
            onQueryComplete={trackQuery}
          />
        </div>

        {/* Stats Panel - Hour 13 */}
        <div className="w-64 min-w-64 border-l border-gray-200 bg-white overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-200 bg-white">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center shadow-md shadow-cyan-500/20">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h2 className="text-lg font-bold text-gray-900">Metrics</h2>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Query Stats */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-xl p-4">
              <div className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-3">Query Performance</div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total Queries</span>
                  <span className="text-lg font-bold text-blue-700">{queryStats.totalQueries}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Avg Latency</span>
                  <span className="text-lg font-bold text-blue-700">{queryStats.avgLatency}ms</span>
                </div>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100 rounded-xl p-4">
              <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-3">System Status</div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <span className="text-sm text-gray-600">WebSocket</span>
                  <span className={`ml-auto text-sm font-medium ${isConnected ? 'text-emerald-600' : 'text-red-600'}`}>
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${status.watcherActive ? 'bg-emerald-500' : 'bg-gray-400'}`} />
                  <span className="text-sm text-gray-600">File Watcher</span>
                  <span className={`ml-auto text-sm font-medium ${status.watcherActive ? 'text-emerald-600' : 'text-gray-500'}`}>
                    {status.watcherActive ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            </div>

            {/* Current Role */}
            <div className={`
              rounded-xl p-4 border
              ${currentRole === 'admin' ? 'bg-gradient-to-br from-purple-50 to-fuchsia-50 border-purple-100' :
                currentRole === 'manager' ? 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-100' :
                'bg-gradient-to-br from-gray-50 to-slate-50 border-gray-200'}
            `}>
              <div className={`text-xs font-semibold uppercase tracking-wider mb-3 ${
                currentRole === 'admin' ? 'text-purple-400' :
                currentRole === 'manager' ? 'text-blue-400' : 'text-gray-400'
              }`}>Access Level</div>
              <div className="flex items-center gap-3">
                <div className={`
                  w-10 h-10 rounded-lg flex items-center justify-center
                  ${currentRole === 'admin' ? 'bg-purple-100 text-purple-600' :
                    currentRole === 'manager' ? 'bg-blue-100 text-blue-600' :
                    'bg-gray-200 text-gray-600'}
                `}>
                  {getRoleIcon(currentRole)}
                </div>
                <div>
                  <div className={`font-bold ${
                    currentRole === 'admin' ? 'text-purple-700' :
                    currentRole === 'manager' ? 'text-blue-700' : 'text-gray-700'
                  }`}>{ROLES[currentRole].label}</div>
                  <div className="text-xs text-gray-500">Level {ROLES[currentRole].level}</div>
                </div>
              </div>
            </div>

            {/* Recent Queries */}
            {queryStats.lastQueries.length > 0 && (
              <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-100 rounded-xl p-4">
                <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-3">Recent Queries</div>
                <div className="space-y-2">
                  {queryStats.lastQueries.slice(0, 5).map((q, i) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Query {queryStats.totalQueries - i}</span>
                      <span className={`font-medium ${q.latency < 300 ? 'text-emerald-600' : q.latency < 600 ? 'text-amber-600' : 'text-red-600'}`}>
                        {q.latency}ms
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Notifications */}
      <SyncNotification notifications={notifications} />
    </div>
  )
}

export default App
