function SyncNotification({ notifications }) {
  if (notifications.length === 0) return null

  return (
    <div className="fixed bottom-6 right-6 z-50 space-y-3 max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`
            flex items-start gap-3 px-4 py-3 rounded-xl shadow-xl backdrop-blur-sm
            animate-slide-in border
            ${notification.type === 'success'
              ? 'bg-green-500/95 text-white border-green-400/50'
              : ''}
            ${notification.type === 'update'
              ? 'bg-blue-500/95 text-white border-blue-400/50'
              : ''}
            ${notification.type === 'error'
              ? 'bg-red-500/95 text-white border-red-400/50'
              : ''}
          `}
        >
          <div className="flex-shrink-0 mt-0.5">
            {notification.type === 'success' && (
              <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            )}
            {notification.type === 'update' && (
              <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>
            )}
            {notification.type === 'error' && (
              <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium leading-snug">{notification.message}</p>
            {notification.file && (
              <p className="text-xs opacity-75 mt-0.5 truncate">{notification.file}</p>
            )}
          </div>
        </div>
      ))}

      <style>{`
        @keyframes slide-in {
          from {
            opacity: 0;
            transform: translateX(100%) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateX(0) scale(1);
          }
        }
        .animate-slide-in {
          animation: slide-in 0.35s cubic-bezier(0.21, 1.02, 0.73, 1);
        }
      `}</style>
    </div>
  )
}

export default SyncNotification
