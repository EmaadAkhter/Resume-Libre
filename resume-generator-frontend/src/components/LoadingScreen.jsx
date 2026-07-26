import { Loader2 } from 'lucide-react'

export default function LoadingScreen({ label = 'Loading...' }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-3 bg-gray-50 text-gray-400">
      <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
      <span className="text-sm">{label}</span>
    </div>
  )
}
