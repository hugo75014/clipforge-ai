import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { User } from '@/types'

interface AuthState {
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  setUser: (user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      setUser: (user) => set({ user }),
      logout: () => {
        localStorage.removeItem('clipforge.token')
        localStorage.removeItem('clipforge.user')
        set({ token: null, user: null })
      },
    }),
    {
      name: 'clipforge-auth',
      storage: createJSONStorage(() => localStorage),
    }
  )
)
