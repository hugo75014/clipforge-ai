import { Navigate, useLocation } from 'react-router-dom'

import AppShell from '@/components/layout/AppShell'
import LandingPage from '@/pages/LandingPage'
import { useAuthStore } from '@/store/auth'

/**
 * Décide ce que voit quelqu'un qui arrive sur « / ».
 *
 * Visiteur : la page de présentation, seule page publique du site.
 * Compte connecté : l'application, exactement comme avant.
 * Visiteur sur une route interne : direction la connexion, avec la page
 * demandée en mémoire pour l'y ramener après.
 */
export default function HomeGate() {
  const { token, user } = useAuthStore()
  const location = useLocation()

  if (token && user) return <AppShell />
  if (location.pathname === '/') return <LandingPage />

  return <Navigate to="/login" state={{ from: location.pathname }} replace />
}
