/**
 * Regional radar-style view: stats-driven risk snapshot with timezone-aware clock.
 */
import { Progress, Statistic, Typography } from "antd"
import { useEffect, useMemo, useState } from "react"
import type { Region } from "../constants/org"
import { REGIONS, REGION_TIMEZONE_OFFSET_HOURS } from "../constants/org"
import { ATTACK_METHOD_LABELS } from "../constants/attackMethodLabels"
import DashboardFiltersBar from "../components/dashboard/DashboardFiltersBar"
import { useDashboardStats } from "../hooks/useDashboardStats"
import { useAuthStore } from "../store/authStore"
import { useOrgStore } from "../store/orgStore"
import RTCard from "../ui/RTCard"
import style from "../Styles/HomePage.module.css"

type StatsShape = {
	total_incidents?: number
	risk_distribution?: Record<string, number>
	top_attack_method?: string
}

function riskIndexFromStats(stats: StatsShape | null): number {
	if (!stats?.total_incidents) return 0
	const d = stats.risk_distribution ?? {}
	const low = Number(d.low ?? 0)
	const med = Number(d.medium ?? 0)
	const high = Number(d.high ?? 0)
	const crit = Number(d.critical ?? 0)
	const weighted = low * 0.15 + med * 0.35 + high * 0.65 + crit * 1.0
	return Math.min(1, weighted / Math.max(stats.total_incidents, 1))
}

export default function RadarPage() {
	const { user } = useAuthStore()
	const { settings, update } = useOrgStore()
	const [region, setRegion] = useState<Region>(settings.region)
	const { stats, loadError } = useDashboardStats<StatsShape>()
	const [now, setNow] = useState(new Date())

	useEffect(() => {
		setRegion(settings.region)
	}, [settings.region])

	useEffect(() => {
		const t = setInterval(() => setNow(new Date()), 1000)
		return () => clearInterval(t)
	}, [])

	const regionalTime = useMemo(() => {
		const d = new Date(now)
		d.setHours(d.getUTCHours() + 3 + REGION_TIMEZONE_OFFSET_HOURS[region])
		return d.toLocaleTimeString("ru-RU", { hour12: false })
	}, [now, region])

	const risk = useMemo(() => riskIndexFromStats(stats), [stats])
	const topMethod = stats?.top_attack_method ?? "malware"
	const topMethodRu = ATTACK_METHOD_LABELS[topMethod] ?? topMethod

	return (
		<div className={style.infraAuditRightColumn}>
			{user ? <DashboardFiltersBar /> : null}
			{loadError ? (
				<RTCard>
					<Typography.Text type="danger">{loadError}</Typography.Text>
				</RTCard>
			) : null}
			<RTCard>
				<div className={style.infraAuditRiskBlock}>
					{risk > 0.55 ? (
						<>
							<Typography.Title level={5}>Повышенный уровень риска по истории</Typography.Title>
							<Typography.Paragraph>
								По данным вашей организации чаще встречается метод: <strong>{topMethodRu}</strong>. См. страницу
								аналитики и раннее предупреждение.
							</Typography.Paragraph>
						</>
					) : (
						<>
							<Typography.Title level={5}>Умеренный / низкий риск</Typography.Title>
							<Typography.Paragraph>
								Сводка по инцидентам в БД для вашей организации. Доминирующий метод: {topMethodRu}.
							</Typography.Paragraph>
						</>
					)}
				</div>
			</RTCard>

			<div className={style.infraAuditRiskRow}>
				<RTCard className={style.infraAuditSmallCard}>
					<Typography.Text>Индекс риска (по данным БД)</Typography.Text>
					<div className={style.infraAuditProgressWrapper}>
						<Progress
							type="dashboard"
							percent={Math.round(risk * 100)}
							strokeColor={risk > 0.55 ? "#FF4F12" : "#7733FF"}
						/>
					</div>
				</RTCard>

				<RTCard className={style.infraAuditSmallCard}>
					<Statistic title="Текущее региональное время (оценка)" value={regionalTime} />

					<div className={style.infraAuditPillRow}>
						{REGIONS.map((r) => (
							<button
								key={r}
								type="button"
								onClick={() => {
									setRegion(r)
									update({ region: r })
								}}
								className={style.infraAuditPillButton}
							>
								{r}
							</button>
						))}
					</div>
				</RTCard>
			</div>
		</div>
	)
}
