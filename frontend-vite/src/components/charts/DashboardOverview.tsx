/**
 * Home dashboard charts: incident trends and breakdowns using `/stats` with filter params.
 */
import { Area, Column, Line, Pie } from "@ant-design/plots"
import { Alert, Spin } from "antd"
import { useMemo } from "react"
// import DashboardFiltersBar from "../dashboard/DashboardFiltersBar"
import { TARGET_OBJECT_LABELS } from "../../constants/targetObjectLabels"
import { useDashboardStats } from "../../hooks/useDashboardStats"
// import { useAuthStore } from "../../store/authStore"
import style from "../../Styles/HomePage.module.css"

const rtPalette = ["#FF4F12", "#001A4D", "#0EA5E9", "#F59E0B", "#22C55E"]

type StatsShape = {
	total_incidents?: number
	incidents_by_hour?: Record<string, number>
	incidents_by_target_object?: Record<string, number>
	incidents_by_season?: Record<string, number>
	incidents_by_time_of_day?: Record<string, number>
	risk_distribution?: Record<string, number>
	top_attack_method?: string
}

const SEASON_ORDER = ["winter", "spring", "summer", "autumn"] as const
const SEASON_RU: Record<string, string> = {
	winter: "Зима",
	spring: "Весна",
	summer: "Лето",
	autumn: "Осень",
}

const TOD_ORDER = ["morning", "afternoon", "evening", "night"] as const
const TOD_RU: Record<string, string> = {
	morning: "Утро",
	afternoon: "День",
	evening: "Вечер",
	night: "Ночь",
}

function hourlySeries(stats: StatsShape | null): { time: string; value: number }[] {
	if (!stats?.incidents_by_hour) return []
	return Array.from({ length: 24 }, (_, h) => ({
		time: `${h}:00`,
		value: Number(stats.incidents_by_hour![h] ?? stats.incidents_by_hour![String(h)] ?? 0),
	}))
}

function targetDistribution(stats: StatsShape | null): { type: string; value: number }[] {
	const raw = stats?.incidents_by_target_object
	if (!raw || Object.keys(raw).length === 0) {
		return [{ type: "Нет данных в выборке", value: 1 }]
	}
	return Object.entries(raw).map(([key, count]) => ({
		type: TARGET_OBJECT_LABELS[key] ?? key,
		value: Number(count),
	}))
}

function seasonTrend(stats: StatsShape | null): { time: string; value: number }[] {
	if (!stats?.incidents_by_season) return []
	return SEASON_ORDER.map((k) => ({
		time: SEASON_RU[k] ?? k,
		value: Number(stats.incidents_by_season![k] ?? 0),
	}))
}

function timeOfDaySeries(stats: StatsShape | null): { x: string; y: number }[] {
	const raw = stats?.incidents_by_time_of_day
	if (!raw) return []
	return TOD_ORDER.map((k) => ({
		x: TOD_RU[k] ?? k,
		y: Number(raw[k] ?? 0),
	}))
}

function highCriticalCount(stats: StatsShape | null): number {
	const d = stats?.risk_distribution
	if (!d) return 0
	return Number(d.high ?? d.HIGH ?? 0) + Number(d.critical ?? d.CRITICAL ?? 0)
}

function maxHourly(stats: StatsShape | null): number {
	const s = hourlySeries(stats)
	return s.reduce((m, p) => Math.max(m, p.value), 0)
}

export default function DashboardOverview() {
	// const { user } = useAuthStore()
	const { stats, loading, loadError } = useDashboardStats<StatsShape>()

	const attacksByHour = useMemo(() => hourlySeries(stats), [stats])
	const anomaliesTrend = useMemo(() => seasonTrend(stats), [stats])
	const distribution = useMemo(() => targetDistribution(stats), [stats])
	const tinyA = useMemo(() => hourlySeries(stats).map((d, i) => ({ x: String(i), y: d.value })), [stats])
	const tinyB = useMemo(() => timeOfDaySeries(stats), [stats])
	const tinyC = useMemo(() => seasonTrend(stats).map((d, i) => ({ x: String(i), y: d.value })), [stats])

	const kpiIncidents = stats?.total_incidents ?? 0
	const kpiElevated = highCriticalCount(stats)
	const kpiPeakHour = maxHourly(stats)

	return (
		<div className={style.page}>
			<div data-report-name="Дашборд">
				<div className={style.container}>
					{/*{user ? <DashboardFiltersBar /> : null}*/}
					{loadError ? (
						<Alert type="warning" message={loadError} showIcon style={{ marginBottom: 16 }} />
					) : null}
					<Spin spinning={loading}>
						<div className={style.stack}>
							<div className={style.grid}>
								<div className={style["col-8"]}>
									<div className={style.panel}>
										<div className={style.panelHeader}>
											Активность атак по часам (данные вашей организации)
										</div>
										<div className={style.chartContainerLg}>
											<Area
												data={attacksByHour}
												xField="time"
												yField="value"
												area={{
													style: {
														fill: "l(270) 0:#FF8A5A 1:#FF4F12",
														fillOpacity: 0.25,
													},
												}}
												line={{
													shape: "smooth",
													style: {
														stroke: rtPalette[0],
														lineWidth: 2,
													},
												}}
												tooltip={{ showMarkers: false }}
												autoFit
											/>
										</div>
									</div>
								</div>

								<div className={style["col-4"]}>
									<div className={style.panel}>
										<div className={style.panelHeader}>Распределение по объектам воздействия</div>
										<div className={style.chartContainerMid}>
											<Pie
												data={distribution}
												angleField="value"
												colorField="type"
												color={rtPalette}
												radius={0.9}
												innerRadius={0.65}
												label={false}
												legend={{ position: "bottom" }}
												autoFit
											/>
										</div>
									</div>
								</div>
							</div>

							<div className={style.grid}>
								<div className={style["col-12"]}>
									<div className={style.panel}>
										<div className={style.panelHeader}>Инциденты по сезонам (та же выборка)</div>
										<div className={style.chartContainer}>
											<Line
												data={anomaliesTrend}
												xField="time"
												yField="value"
												color={rtPalette[1]}
												smooth
												lineStyle={{ lineWidth: 2 }}
												autoFit
											/>
										</div>
									</div>
								</div>
							</div>

							<div className={style.grid}>
								<div className={style["col-12"]}>
									<div className={style.panel}>
										<div className={style.panelHeader}>Ключевые метрики</div>
										<div className={style.kpiRow}>
											<div className={style.kpiBox}>
												<div className={style.kpiLabel}>Инциденты в выборке</div>
												<div className={style.kpiValue}>{kpiIncidents}</div>
												<div className={style.sparkline}>
													<Line
														data={tinyA}
														xField="x"
														yField="y"
														autoFit
														color={rtPalette[0]}
														lineStyle={{ lineWidth: 2 }}
														padding={[2, 4, 2, 4]}
													/>
												</div>
											</div>

											<div className={style.kpiBox}>
												<div className={style.kpiLabel}>Повышенный риск (high + critical)</div>
												<div className={style.kpiValue}>{kpiElevated}</div>
												<div className={style.sparkline}>
													<Column
														data={tinyB}
														xField="x"
														yField="y"
														autoFit
														color={rtPalette[2]}
														padding={[2, 4, 2, 4]}
													/>
												</div>
											</div>

											<div className={style.kpiBox}>
												<div className={style.kpiLabel}>Пик интенсивности (инц. в один час)</div>
												<div className={style.kpiValue}>{kpiPeakHour}</div>
												<div className={style.sparkline}>
													<Line
														data={tinyC}
														xField="x"
														yField="y"
														autoFit
														color={rtPalette[1]}
														lineStyle={{ lineWidth: 2 }}
														padding={[2, 4, 2, 4]}
													/>
												</div>
											</div>
										</div>
									</div>
								</div>
							</div>
						</div>
					</Spin>
				</div>
			</div>
		</div>
	)
}
