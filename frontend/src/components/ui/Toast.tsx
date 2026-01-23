import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  message: string
  type: ToastType
  duration?: number
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (message: string, type?: ToastType, duration?: number) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((message: string, type: ToastType = 'info', duration = 4000) => {
    const id = Math.random().toString(36).substring(2, 9)
    setToasts((prev) => [...prev, { id, message, type, duration }])

    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
      }, duration)
    }
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

function ToastContainer({ toasts, removeToast }: { toasts: Toast[]; removeToast: (id: string) => void }) {
  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={() => removeToast(toast.id)} />
      ))}
    </div>
  )
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  }

  const styles = {
    success: {
      bg: 'bg-green-500/10 border-green-500/30',
      icon: 'text-green-400',
      text: 'text-green-300',
    },
    error: {
      bg: 'bg-red-500/10 border-red-500/30',
      icon: 'text-red-400',
      text: 'text-red-300',
    },
    warning: {
      bg: 'bg-yellow-500/10 border-yellow-500/30',
      icon: 'text-yellow-400',
      text: 'text-yellow-300',
    },
    info: {
      bg: 'bg-blue-500/10 border-blue-500/30',
      icon: 'text-blue-400',
      text: 'text-blue-300',
    },
  }

  const Icon = icons[toast.type]
  const style = styles[toast.type]

  return (
    <div
      className={cn(
        'flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm',
        'animate-slide-in-from-right animate-fade-in',
        'min-w-[300px] max-w-[400px]',
        style.bg
      )}
    >
      <Icon className={cn('h-5 w-5 flex-shrink-0', style.icon)} />
      <p className={cn('flex-1 text-sm', style.text)}>{toast.message}</p>
      <button
        onClick={onRemove}
        className="p-1 rounded hover:bg-white/10 transition-colors"
      >
        <X className="h-4 w-4 text-gray-400" />
      </button>
    </div>
  )
}
