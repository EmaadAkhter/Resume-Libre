import { useState, useEffect } from 'react'
import { Check, AlertCircle, X, Info } from 'lucide-react'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

export default function ToastContainer() {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    const handleShow = (data) => {
      const id = Date.now() + Math.random()
      const toast = {
        id,
        type: data.type || 'info',
        message: data.message,
        duration: data.duration || (data.type === 'error' ? 5000 : 3000),
      }
      setToasts((prev) => [...prev, toast])

      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
      }, toast.duration)
    }

    const handleDismiss = (id) => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }

    eventBus.on(EVENTS.NOTIFICATION_SHOW, handleShow)
    eventBus.on(EVENTS.NOTIFICATION_DISMISS, handleDismiss)

    return () => {
      eventBus.off(EVENTS.NOTIFICATION_SHOW, handleShow)
      eventBus.off(EVENTS.NOTIFICATION_DISMISS, handleDismiss)
    }
  }, [])

  const dismiss = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  const icons = {
    success: <Check className="w-5 h-5 text-green-600" />,
    error: <AlertCircle className="w-5 h-5 text-red-600" />,
    info: <Info className="w-5 h-5 text-blue-600" />,
  }

  const bg = {
    success: 'bg-green-50 border-green-200 text-green-700',
    error: 'bg-red-50 border-red-200 text-red-700',
    info: 'bg-blue-50 border-blue-200 text-blue-700',
  }

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg border ${bg[toast.type]} animate-in`}
        >
          {icons[toast.type]}
          <span className="text-sm flex-1">{toast.message}</span>
          <button onClick={() => dismiss(toast.id)} className="text-gray-400 hover:text-gray-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  )
}
