import { useState, useEffect } from 'react'

function DocumentPane({ documents, status, onRefresh, recentlyUpdated = [] }) {
  const [isIngesting, setIsIngesting] = useState(false)
  const [expandedFolders, setExpandedFolders] = useState({})

  // Auto-expand all folders initially
  useEffect(() => {
    const folders = documents.reduce((acc, doc) => {
      const parts = doc.split('/')
      const folder = parts.length > 1 ? parts[0] : 'root'
      acc[folder] = true
      return acc
    }, {})
    setExpandedFolders(folders)
  }, [documents])

  const handleIngest = async () => {
    setIsIngesting(true)
    try {
      const response = await fetch('http://localhost:8000/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory: '/Users/abhinavsaha/Desktop/retriever/documents' }),
      })
      const data = await response.json()
      console.log('Ingestion complete:', data)
      onRefresh()
    } catch (error) {
      console.error('Ingestion failed:', error)
    } finally {
      setIsIngesting(false)
    }
  }

  const toggleFolder = (folder) => {
    setExpandedFolders(prev => ({
      ...prev,
      [folder]: !prev[folder]
    }))
  }

  // Group documents by folder
  const groupedDocs = documents.reduce((acc, doc) => {
    const parts = doc.split('/')
    const folder = parts.length > 1 ? parts[0] : 'root'
    if (!acc[folder]) acc[folder] = []
    acc[folder].push(doc)
    return acc
  }, {})

  const formatTime = (isoString) => {
    if (!isoString) return 'Never'
    const date = new Date(isoString)
    const now = new Date()
    const diffSeconds = Math.floor((now - date) / 1000)

    if (diffSeconds < 5) return 'Just now'
    if (diffSeconds < 60) return `${diffSeconds}s ago`
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`
    return date.toLocaleTimeString()
  }

  const isRecentlyUpdated = (file) => {
    return recentlyUpdated.some(f => file.endsWith(f) || f.endsWith(file))
  }

  const getFileIcon = (fileName) => {
    if (fileName.endsWith('.md') || fileName.endsWith('.markdown')) {
      return (
        <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    }
    return (
      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    )
  }

  const getFolderIcon = (folder) => {
    const colors = {
      policies: 'text-purple-500',
      product: 'text-green-500',
      faq: 'text-orange-500',
      root: 'text-gray-500',
    }
    return colors[folder] || 'text-gray-400'
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <div className="p-5 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-md shadow-indigo-500/20">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <h2 className="text-lg font-bold text-gray-900">Documents</h2>
          </div>
          <button
            onClick={handleIngest}
            disabled={isIngesting}
            className={`
              px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 transition-all shadow-sm
              ${isIngesting
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700 shadow-blue-500/25 hover:shadow-md'}
            `}
          >
            {isIngesting ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Ingesting...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Re-index
              </>
            )}
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-xl p-3 text-center shadow-sm">
            <div className="text-xl font-bold text-blue-700">{documents.length}</div>
            <div className="text-xs text-blue-500 font-medium">Files</div>
          </div>
          <div className="bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100 rounded-xl p-3 text-center shadow-sm">
            <div className="text-xl font-bold text-emerald-700">{status.documentsIndexed}</div>
            <div className="text-xs text-emerald-500 font-medium">Chunks</div>
          </div>
          <div className="bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-100 rounded-xl p-3 text-center shadow-sm">
            <div className="text-xl font-bold text-orange-700">{Object.keys(groupedDocs).length}</div>
            <div className="text-xs text-orange-500 font-medium">Folders</div>
          </div>
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto">
        {Object.keys(groupedDocs).length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="font-medium">No documents indexed</p>
            <p className="text-sm mt-1">Click "Re-index" to scan and index documents</p>
          </div>
        ) : (
          <div className="py-2">
            {Object.entries(groupedDocs).map(([folder, files]) => (
              <div key={folder} className="mb-1">
                {/* Folder Header */}
                <button
                  onClick={() => toggleFolder(folder)}
                  className="w-full flex items-center gap-2 px-4 py-2 hover:bg-gray-50 transition-colors"
                >
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${expandedFolders[folder] ? 'rotate-90' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <svg className={`w-4 h-4 ${getFolderIcon(folder)}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                  <span className="text-sm font-medium text-gray-700">{folder}</span>
                  <span className="ml-auto text-xs text-gray-400">{files.length}</span>
                </button>

                {/* Files */}
                {expandedFolders[folder] && (
                  <div className="ml-8">
                    {files.map((file) => {
                      const fileName = file.split('/').pop()
                      const isUpdated = isRecentlyUpdated(file)
                      return (
                        <div
                          key={file}
                          className={`
                            flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer group
                            transition-all duration-300
                            ${isUpdated
                              ? 'bg-green-50 border-l-2 border-green-500'
                              : 'hover:bg-gray-50 border-l-2 border-transparent'
                            }
                          `}
                        >
                          {getFileIcon(fileName)}
                          <span className={`text-sm ${isUpdated ? 'text-green-700 font-medium' : 'text-gray-600 group-hover:text-gray-900'}`}>
                            {fileName}
                          </span>
                          {isUpdated ? (
                            <span className="ml-auto text-xs text-green-600 flex items-center gap-1">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              Updated
                            </span>
                          ) : (
                            <span className="ml-auto text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
                              indexed
                            </span>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer - Watcher Status */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className={`
          flex items-center justify-between p-3 rounded-xl border transition-all
          ${status.watcherActive
            ? 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200'
            : 'bg-gray-50 border-gray-200'}
        `}>
          <div className="flex items-center gap-3">
            <div className={`
              w-9 h-9 rounded-lg flex items-center justify-center
              ${status.watcherActive ? 'bg-emerald-100' : 'bg-gray-200'}
            `}>
              <div className="relative">
                <span className={`w-3 h-3 rounded-full block ${status.watcherActive ? 'bg-emerald-500' : 'bg-gray-400'}`} />
                {status.watcherActive && (
                  <span className="absolute inset-0 w-3 h-3 rounded-full bg-emerald-500 animate-ping opacity-50" />
                )}
              </div>
            </div>
            <div>
              <div className={`text-sm font-semibold ${status.watcherActive ? 'text-emerald-700' : 'text-gray-500'}`}>
                {status.watcherActive ? 'Watching for changes' : 'Watcher inactive'}
              </div>
              <div className={`text-xs ${status.watcherActive ? 'text-emerald-500' : 'text-gray-400'}`}>
                Last sync: {formatTime(status.lastSync)}
              </div>
            </div>
          </div>
          <button
            onClick={onRefresh}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-white rounded-lg transition-all"
            title="Refresh"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

export default DocumentPane
