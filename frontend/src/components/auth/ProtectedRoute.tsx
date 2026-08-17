import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  requireAdmin?: boolean
}

export default function ProtectedRoute({ children, requireAdmin = false }: Props) {
  const { token, user } = useAuthStore()
  const location = useLocation()
  if (!token || !user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }
  if (requireAdmin && user.role !== 'admin') {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}
