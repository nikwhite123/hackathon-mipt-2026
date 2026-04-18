/**
 * Historical trends tab: Recharts time series fed by filtered `/stats` aggregates.
 */
import { Card, Spin, Typography, Alert } from "antd"
import { useMemo } from "react"
import {
	Area,
	AreaChart,
	Bar,
	BarChart,
	CartesianGrid,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts"
import DashboardFiltersBar from "../dashboard/DashboardFiltersBar"
import { TARGET_OBJECT_LABELS } from "../../constants/targetObjectLabels"
import { useDashboardStats } from "../../hooks/useDashboardStats"
import { useAuthStore } from "../../store/authStore"

const { Title } = Typography

type StatsPayload = {
	total_incidents?: number
	incidents_by_month?: Record<string, number>
	incidents_by_target_object?: Record<string, number>
}

type Props = {
	hideFilters?: boolean
}

export default function HistoricalDashboard({ hideFilters = false }: Props) {
	const { user } = useAuthStore()
	const { stats, loading, loadError: error } = useDashboardStats<StatsPayload>()

	const areaData = useMemo(() => {
		const raw = stats?.incidents_by_month
		if (!raw || Object.keys(raw).length === 0) return []
		return Object.keys(raw)
			.sort()
			.map((ym) => ({ date: ym, incidents: Number(raw[ym]) }))
	}, [stats])

	const barData = useMemo(() => {
		const raw = stats?.incidents_by_target_object
		if (!raw) return []
		return Object.entries(raw).map(([key, attacks]) => ({
			object: TARGET_OBJECT_LABELS[key] ?? key,
			attacks: Number(attacks),
		}))
	}, [stats])

	return (
		<div style={{ padding: 24, maxWidth: 1200, margin: "0 auto" }}>
			<Title level={2}>Дашборд исторической аналитики</Title>
			<Typography.Paragraph type="secondary">
				Данные из базы по организации, в которой вы зарегистрированы.
				{hideFilters
					? " Фильтры выборки заданы на вкладке «Обзор»."
					: " Фильтры уходят в SQL на сервере."}
			</Typography.Paragraph>

			{!hideFilters && user ? <DashboardFiltersBar /> : null}
			{error ? <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} /> : null}

			<Spin spinning={loading}>
				<Card style={{ marginBottom: 24, borderRadius: 12, padding: 20 }}>
					<Title level={4}>Инциденты по месяцам (выборка)</Title>
					{areaData.length === 0 ? (
						<Typography.Text type="secondary">Нет дат инцидентов для построения ряда.</Typography.Text>
					) : (
						<ResponsiveContainer width="100%" height={300}>
							<AreaChart data={areaData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
								<defs>
									<linearGradient id="colorIncidents" x1="0" y1="0" x2="0" y2="1">
										<stop offset="5%" stopColor="#7733FF" stopOpacity={0.5} />
										<stop offset="95%" stopColor="#7733FF" stopOpacity={0.05} />
									</linearGradient>
								</defs>
								<CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
								<XAxis dataKey="date" tick={{ fontSize: 12, fill: "#666" }} tickLine={false} axisLine={false} />
								<YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#666" }} tickLine={false} axisLine={false} />
								<Tooltip />
								<Area type="monotone" dataKey="incidents" stroke="#7733FF" fill="url(#colorIncidents)" />
							</AreaChart>
						</ResponsiveContainer>
					)}
				</Card>

				<Card style={{ borderRadius: 12, padding: 20 }}>
					<Title level={4}>Распределение по объектам воздействия</Title>
					{barData.length === 0 ? (
						<Typography.Text type="secondary">Нет данных.</Typography.Text>
					) : (
						<ResponsiveContainer width="100%" height={280}>
							<BarChart data={barData}>
								<CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
								<XAxis dataKey="object" tick={{ fontSize: 11, fill: "#666" }} axisLine={false} tickLine={false} />
								<YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#666" }} axisLine={false} tickLine={false} />
								<Tooltip />
								<Bar dataKey="attacks" fill="#FF4F12" radius={[6, 6, 0, 0]} />
							</BarChart>
						</ResponsiveContainer>
					)}
				</Card>
			</Spin>
		</div>
	)
}
