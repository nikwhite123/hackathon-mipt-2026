/**
 * Shared Axios client: JSON API base URL, Bearer token from localStorage, clears token on 401.
 */
import axios from 'axios'
import { getApiBaseUrl } from './config'
import { useAuthStore } from '../store/authStore'
import { useOrgStore } from '../store/orgStore'
import { useDashboardFiltersStore } from '../store/dashboardFiltersStore'

const TOKEN_STORAGE_KEY = 'rt-auth-token'

export function getAuthToken(): string | null {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setAuthToken(token: string) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearAuthToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY)
}

export function clearClientSession() {
  clearAuthToken()
  useAuthStore.getState().setUser(null)
  useOrgStore.getState().reset()
  useDashboardFiltersStore.getState().reset()
}

const axiosClient = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
})

axiosClient.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axiosClient.interceptors.response.use(
  (response) => response,
  (error: { response?: { data?: unknown; status?: number }; message: string }) => {
    if (error.response?.status === 401) {
      clearClientSession()
    }
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  },
)

export default axiosClient
