/**
 * Analytics stats (`GET /stats`) and facet lists for dashboard filters (`GET /stats/facets`).
 */
import axiosClient from "./axiosClient"

export const fetchStats = async (params?: Record<string, string | number>) => {
	const response = await axiosClient.get("/stats", { params: params ?? {} })
	return response.data
}

export type StatsFacets = { regions: string[]; industries: string[] }

export const fetchStatsFacets = async (): Promise<StatsFacets> => {
	const { data } = await axiosClient.get<StatsFacets>("/stats/facets")
	return data
}
