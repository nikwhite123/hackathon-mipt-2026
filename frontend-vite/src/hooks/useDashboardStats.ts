/**
 * Loads GET /stats for the signed-in user: optional dashboard filter params or raw org aggregate.
 */
import { useEffect, useState } from "react"
import { fetchStats } from "../api/analyticsService"
import { useAuthStore } from "../store/authStore"
import { toStatsQueryParams, useDashboardFiltersStore } from "../store/dashboardFiltersStore"
import { getApiErrorDetail } from "../utils/apiError"

const DEFAULT_STATS_ERROR = "Failed to load statistics"

export type UseDashboardStatsOptions = {
	/**
	 * When true (default), forwards `toStatsQueryParams` from the dashboard filter store.
	 * When false, calls `/stats` with no filters (legacy widgets on the home dashboard).
	 */
	applyDashboardFilters?: boolean
}

export function useDashboardStats<T extends Record<string, unknown> = Record<string, unknown>>(
	options: UseDashboardStatsOptions = {},
) {
	const { applyDashboardFilters = true } = options
	const { user } = useAuthStore()
	const filterRevision = useDashboardFiltersStore((s) => s.revision)
	/** When filters are off, hold revision at 0 so filter changes do not refetch unfiltered widgets. */
	const revisionToken = applyDashboardFilters ? filterRevision : 0
	const [stats, setStats] = useState<T | null>(null)
	const [loading, setLoading] = useState(false)
	const [loadError, setLoadError] = useState<string | null>(null)

	useEffect(() => {
		if (!user) {
			setStats(null)
			setLoadError(null)
			setLoading(false)
			return
		}
		let cancelled = false
		setLoading(true)
		setLoadError(null)
		const params = applyDashboardFilters ? toStatsQueryParams(useDashboardFiltersStore.getState()) : {}
		fetchStats(params)
			.then((data) => {
				if (!cancelled) setStats(data as T)
			})
			.catch((err: unknown) => {
				if (!cancelled) {
					setLoadError(getApiErrorDetail(err, DEFAULT_STATS_ERROR))
					setStats(null)
				}
			})
			.finally(() => {
				if (!cancelled) setLoading(false)
			})
		return () => {
			cancelled = true
		}
	}, [user, revisionToken, applyDashboardFilters])

	return { stats, loading, loadError }
}
