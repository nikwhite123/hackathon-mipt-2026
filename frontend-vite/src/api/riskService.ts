import axiosClient from './axiosClient'
import { backendEnabled } from './config'

export type ThreatForecast = {
	id: string
	target: string
	method: string
	probability: number
	etaMinutes: number
}

export async function fetchThreatForecast(): Promise<ThreatForecast> {
	if (backendEnabled) {
		const { data } = await axiosClient.get('/forecast/next')
		return data
	}
	await new Promise((r) => setTimeout(r, 200))
	return {
		id: 'TST-001',
		target: 'CRM-сервер',
		method: 'Brute-force',
		probability: 0.72,
		etaMinutes: 43
	}
}

