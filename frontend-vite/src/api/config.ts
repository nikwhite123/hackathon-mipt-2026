/**
 * API base URL from Vite (`VITE_API_URL`) or Node (`REACT_APP_API_URL`), plus backend toggle flags.
 */
const viteEnv =
  typeof import.meta !== 'undefined'
    ? (import.meta as { env?: Record<string, string | undefined> }).env
    : undefined

function getNodeEnv(): Record<string, string | undefined> | undefined {
  if (typeof globalThis === 'undefined' || !('process' in globalThis)) return undefined
  return (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env
}

const nodeEnv = getNodeEnv()

export const backendEnabled =
  viteEnv?.VITE_BACKEND === 'false' || nodeEnv?.REACT_APP_BACKEND === 'false' ? false : true

const DEFAULT_API_URL = 'http://127.0.0.1:8000'

export function getApiBaseUrl(): string {
  const fromVite = viteEnv?.VITE_API_URL
  if (fromVite !== undefined && fromVite !== null && String(fromVite).trim() !== '') {
    return String(fromVite).trim()
  }
  return nodeEnv?.REACT_APP_API_URL || DEFAULT_API_URL
}

export const API_BASE_URL = getApiBaseUrl()
