const viteEnv =
	typeof import.meta !== 'undefined' ? (import.meta as { env?: Record<string, string | undefined> }).env : undefined

function getNodeEnv(): Record<string, string | undefined> | undefined {
	if (typeof globalThis === 'undefined' || !('process' in globalThis)) return undefined
	return (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env
}

const nodeEnv = getNodeEnv()

export const backendEnabled =
	Boolean(viteEnv?.VITE_BACKEND === 'true' || nodeEnv?.REACT_APP_BACKEND === 'true')

export function getApiBaseUrl(): string {
	return (
		viteEnv?.VITE_API_URL ||
		nodeEnv?.REACT_APP_API_URL ||
		'http://localhost:8000/api'
	)
}

