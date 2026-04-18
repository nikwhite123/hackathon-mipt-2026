/**
 * Fetches `/stats` when the user is logged in, driven by dashboard filter revision.
 * Derives pie-style distribution rows and surfaces load errors (toast + state).
 */
import { message } from "antd"
import { useEffect, useMemo, useRef } from "react"
import { useDashboardStats } from "./useDashboardStats"

function deriveDistData(stats: Record<string, unknown> | null): { category: string; count: number }[] {
	if (!stats) return []
	const rd = stats.risk_distribution as Record<string, number> | undefined
	if (!rd) return []
	return Object.entries(rd).map(([key, value]) => ({
		category: key.toUpperCase(),
		count: value as number,
	}))
}

export function useAnalyticsStats() {
	const { stats, loading, loadError } = useDashboardStats<Record<string, unknown>>()
	const distData = useMemo(() => deriveDistData(stats), [stats])
	const prevErr = useRef<string | null>(null)

	useEffect(() => {
		if (loadError && loadError !== prevErr.current) {
			prevErr.current = loadError
			console.error("Stats load failed:", loadError)
			message.error(loadError)
		}
		if (!loadError) prevErr.current = null
	}, [loadError])

	return { stats, distData, loading, loadError }
}
