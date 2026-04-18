/**
 * Global auth state: current user or null after SessionProvider hydration.
 */
import { create } from 'zustand'
import type { AuthUser } from '../types/auth'

type AuthState = {
  user: AuthUser | null
  setUser: (user: AuthUser | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}))
