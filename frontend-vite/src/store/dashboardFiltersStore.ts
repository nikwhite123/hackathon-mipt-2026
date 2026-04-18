/**
 * Analytics dashboard filter state and `revision` to refetch `/stats` when filters change.
 */
import { create } from "zustand"

export type SuccessFilter = "" | "0" | "1"

export type DashboardFiltersState = {
	dateFrom: string | null
	dateTo: string | null
	region: string | undefined
	industry: string | undefined
	success: SuccessFilter
	timeOfDay: "" | "night" | "morning" | "afternoon" | "evening"
	season: "" | "winter" | "spring" | "summer" | "autumn"
	attackMethod: string
	filtersPanelExpanded: boolean
	revision: number
	setPatch: (
		patch: Partial<
			Omit<DashboardFiltersState, "setPatch" | "reset" | "revision" | "toggleFiltersPanel" | "filtersPanelExpanded">
		>,
	) => void
	toggleFiltersPanel: () => void
	reset: () => void
}

export type DashboardFilterQuerySlice = Pick<
	DashboardFiltersState,
	"dateFrom" | "dateTo" | "region" | "industry" | "success" | "timeOfDay" | "season" | "attackMethod"
>

const empty: Omit<DashboardFiltersState, "setPatch" | "reset" | "revision" | "toggleFiltersPanel" | "filtersPanelExpanded"> = {
	dateFrom: null,
	dateTo: null,
	region: undefined,
	industry: undefined,
	success: "",
	timeOfDay: "",
	season: "",
	attackMethod: "",
}

export const useDashboardFiltersStore = create<DashboardFiltersState>((set) => ({
	...empty,
	filtersPanelExpanded: true,
	revision: 0,
	setPatch: (patch) =>
		set((s) => ({
			...s,
			...patch,
			revision: s.revision + 1,
		})),
	toggleFiltersPanel: () => set((s) => ({ filtersPanelExpanded: !s.filtersPanelExpanded })),
	reset: () =>
		set((s) => ({
			...empty,
			filtersPanelExpanded: true,
			revision: s.revision + 1,
		})),
}))

export function toStatsQueryParams(s: DashboardFilterQuerySlice): Record<string, string | number> {
	const p: Record<string, string | number> = {}
	if (s.dateFrom) p.date_from = s.dateFrom
	if (s.dateTo) p.date_to = s.dateTo
	if (s.region) p.region = s.region
	if (s.industry) p.industry = s.industry
	if (s.success === "0" || s.success === "1") p.success = Number(s.success)
	if (s.timeOfDay) p.time_of_day = s.timeOfDay
	if (s.season) p.season = s.season
	if (s.attackMethod) p.attack_method = s.attackMethod
	return p
}
