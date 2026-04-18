/**
 * Analytics tab “overview”: heatmap, distributions, and KPI cards from `/stats` hook data.
 */
import { Heatmap, Column } from "@ant-design/plots"
import { Alert, Spin } from "antd"
import { useAnalyticsStats } from "../../hooks/useAnalyticsStats"
import RTCard from "../../ui/RTCard"
import { Grid, GridItem } from "../../ui/Grid"
import cls from "../../Styles/rt.module.css"

const RT_ORANGE = "#FF4F12"
const RT_PURPLE = "#7733FF"
const RT_DARK = "#101828"

function makeHeatmapData(hourly: Record<string, number> | undefined) {
	const defaultDay = "Текущая выборка"
	return Object.entries(hourly ?? {}).map(([hour, value]) => ({
		day: defaultDay,
		hour: `${hour.toString().padStart(2, "0")}:00`,
		value,
	}))
}

export default function AnalyticsOverviewPanel() {
	const { stats, distData, loading, loadError } = useAnalyticsStats()

	return (
		<div className={cls.stack16}>
			{loadError ? <Alert type="error" message="Статистика недоступна" description={loadError} showIcon /> : null}
			<Spin spinning={loading}>
				<Grid>
					<GridItem className={cls["col-4"]}>
						<RTCard title="Всего инцидентов">
							<h2 style={{ fontSize: "2.5rem", margin: 0, color: RT_PURPLE }}>{Number(stats?.total_incidents ?? 0)}</h2>
						</RTCard>
					</GridItem>
					<GridItem className={cls["col-4"]}>
						<RTCard title="Топ метод">
							<h2 style={{ color: RT_ORANGE, fontSize: "2.5rem", margin: 0, fontWeight: "bold" }}>
								{String(stats?.top_attack_method ?? "—").toUpperCase()}
							</h2>
						</RTCard>
					</GridItem>
					<GridItem className={cls["col-4"]}>
						<RTCard title="Главная цель">
							<h2 style={{ color: RT_DARK, fontSize: "2.5rem", margin: 0 }}>
								{String(stats?.top_target_object ?? "—").toUpperCase()}
							</h2>
						</RTCard>
					</GridItem>
				</Grid>

				<Grid>
					<GridItem className={cls["col-8"]}>
						<RTCard title="Активность атак (Карта интенсивности)">
							<div style={{ height: 350 }}>
								<Heatmap
									data={makeHeatmapData(stats?.incidents_by_hour as Record<string, number> | undefined)}
									xField="hour"
									yField="day"
									colorField="value"
									autoFit
									color={["#ffffff", RT_PURPLE]}
								/>
							</div>
						</RTCard>
					</GridItem>

					<GridItem className={cls["col-4"]}>
						<RTCard title="Распределение рисков">
							<div style={{ height: 350 }}>
								<Column
									data={distData}
									xField="category"
									yField="count"
									autoFit
									color={({ category }: { category: string }) =>
										category === "CRITICAL" || category === "HIGH" ? RT_ORANGE : RT_PURPLE
									}
									columnStyle={{
										radius: [4, 4, 0, 0],
									}}
								/>
							</div>
						</RTCard>
					</GridItem>
				</Grid>
			</Spin>
		</div>
	)
}
