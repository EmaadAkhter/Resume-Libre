import { useState, useEffect, useRef } from 'react'
import { AlertCircle } from 'lucide-react'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

export default function BackendStatusBanner() {
  const [status, setStatus] = useState('checking')
  const failCount = useRef(0)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/health`, {
          signal: AbortSignal.timeout(5000),
        })
        if (response.ok) {
          failCount.current = 0
          setStatus('connected')
          eventBus.emit(EVENTS.BACKEND_CONNECTED)
        } else {
          failCount.current++
          if (failCount.current >= 2) {
            setStatus('error')
            eventBus.emit(EVENTS.BACKEND_DISCONNECTED)
          }
        }
      } catch {
        failCount.current++
        if (failCount.current >= 2) {
          setStatus('disconnected')
          eventBus.emit(EVENTS.BACKEND_DISCONNECTED)
        }
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000)

    return () => clearInterval(interval)
  }, [])

  if (status === 'connected' || status === 'checking') return null

  return (
    <div className="fixed top-4 left-4 right-4 bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2 text-sm">
      <AlertCircle className="w-5 h-5 flex-shrink-0" />
      {status === 'disconnected'
        ? 'Backend server is not connected. Make sure it is running.'
        : 'Backend server error.'}
    </div>
  )
}
