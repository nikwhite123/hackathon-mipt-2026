import axiosClient from './axiosClient'
import { backendEnabled } from './config'

export type AnalyticsFilters = {
	season: string
	threatType: string
}

export async function fetchHeatmap(filters: AnalyticsFilters) {
	if (backendEnabled) {
		const { data } = await axiosClient.get<unknown[]>('/analytics/heatmap', { params: filters })
		return data
	}
	await new Promise((r) => setTimeout(r, 200))
	return []
}

export async function fetchDistribution(filters: AnalyticsFilters) {
	if (backendEnabled) {
		const { data } = await axiosClient.get<unknown[]>('/analytics/distribution', { params: filters })
		return data
	}
	await new Promise((r) => setTimeout(r, 200))
	return []
}

