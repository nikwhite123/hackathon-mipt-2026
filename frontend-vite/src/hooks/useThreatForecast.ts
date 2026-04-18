/**
 * Fetches POST /predict payload via `fetchThreatForecast` when `enabled` and org context exist.
 */
import { useEffect, useState } from "react"
import { fetchThreatForecast } from "../api/riskService"
import { useAuthStore } from "../store/authStore"
import { useOrgStore } from "../store/orgStore"
import type { IPredictionResponse } from "../types/incident.types"
import { getApiErrorDetail } from "../utils/apiError"

const DEFAULT_ERROR = "Не удалось загрузить прогноз"
const NO_ORG_CODE = "Не задан код организации для запроса прогноза. Выйдите и войдите снова."

export type UseThreatForecastOptions = {
	enabled: boolean
	/** Set by an explicit UI action when the user requests ML-derived method/target. */
	preferMl?: boolean
}

export function useThreatForecast({ enabled, preferMl = false }: UseThreatForecastOptions) {
	const { user } = useAuthStore()
	const { settings, organizationCode } = useOrgStore()
	const [data, setData] = useState<IPredictionResponse | null>(null)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)

	useEffect(() => {
		if (!enabled || !user) {
			setData(null)
			setError(null)
			setLoading(false)
			return
		}
		if (!organizationCode) {
			setData(null)
			setError(NO_ORG_CODE)
			setLoading(false)
			return
		}

		let cancelled = false
		setLoading(true)
		setError(null)
		fetchThreatForecast(settings, organizationCode, { preferMl })
			.then((res) => {
				if (!cancelled) setData(res)
			})
			.catch((err: unknown) => {
				if (!cancelled) {
					setError(getApiErrorDetail(err, DEFAULT_ERROR))
					setData(null)
				}
			})
			.finally(() => {
				if (!cancelled) setLoading(false)
			})
		return () => {
			cancelled = true
		}
	}, [enabled, user, organizationCode, settings, preferMl])

	return { data, loading, error }
}
