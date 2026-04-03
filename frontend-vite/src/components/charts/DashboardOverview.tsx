import { Area, Column, Line, Pie } from "@ant-design/plots"
import cls from "../../Styles/rt.module.css"

function makeSeries(points = 24) {
	const data: { time: string; value: number }[] = []
	for (let i = 0; i < points; i++) {
		data.push({ time: `${i}:00`, value: Math.round(20 + Math.random() * 80) })
	}
	return data
}

const rtPalette = ['#FF4F12', '#001A4D', '#0EA5E9', '#F59E0B', '#22C55E']

export default function DashboardOverview() {
	const attacksByHour = makeSeries(24)
	const anomaliesTrend = makeSeries(30)
	const distribution = [
		{ type: 'Серверы', value: 38 },
		{ type: 'Сеть', value: 26 },
		{ type: 'БД', value: 22 },
		{ type: 'Веб', value: 14 }
	]
	const tinyA = makeSeries(14).map((d, i) => ({ x: String(i), y: d.value }))
	const tinyB = makeSeries(14).map((d, i) => ({ x: String(i), y: d.value * (0.6 + Math.random() * 0.4) }))
	const tinyC = makeSeries(14).map((d, i) => ({ x: String(i), y: d.value * (0.4 + Math.random() * 0.6) }))

	return (
		<div className={cls.stack16}>
			<div className={cls.grid}>
				<div className={cls["col-8"]}>
					<div className={cls.panel}>
						<div className={cls.panelHeader}>Активность атак по часам</div>
						<div className={cls.chartBoxLg}>
							<Area
								data={attacksByHour}
								xField="time"
								yField="value"
								area={{
									style: {
										fill: "l(270) 0:#FF8A5A 1:#FF4F12",
										fillOpacity: 0.25
									}
								}}
								line={{
									shape: "smooth",
									style: {
										stroke: rtPalette[0],
										lineWidth: 2
									}
								}}
								tooltip={{ showMarkers: false }}
							/>
						</div>
					</div>
				</div>
				<div className={cls["col-4"]}>
					<div className={cls.panel}>
						<div className={cls.panelHeader}>Ключевые метрики</div>
						<div className={cls.kpiRow}>
							<div className={cls.kpiBox}>
								<div className={cls.kpiLabel}>Атаки/сутки</div>
								<div className={cls.kpiValue}>124</div>
								<div className={cls.sparkline}>
									<Line
										data={tinyA}
										xField="x"
										yField="y"
										height={52}
										padding={[2, 4, 2, 4]}
										autoFit
										color={rtPalette[0]}
										lineStyle={{ lineWidth: 2 }}
									/>
								</div>
							</div>
							<div className={cls.kpiBox}>
								<div className={cls.kpiLabel}>Аномалии</div>
								<div className={cls.kpiValue}>58</div>
								<div className={cls.sparkline}>
									<Column
										data={tinyB}
										xField="x"
										yField="y"
										height={52}
										padding={[2, 4, 2, 4]}
										autoFit
										color={rtPalette[2]}
									/>
								</div>
							</div>
							<div className={cls.kpiBox}>
								<div className={cls.kpiLabel}>Инциденты</div>
								<div className={cls.kpiValue}>7</div>
								<div className={cls.sparkline}>
									<Line
										data={tinyC}
										xField="x"
										yField="y"
										height={52}
										padding={[2, 4, 2, 4]}
										autoFit
										color={rtPalette[1]}
										lineStyle={{ lineWidth: 2 }}
									/>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div className={cls.grid}>
				<div className={cls["col-6"]}>
					<div className={cls.panel}>
						<div className={cls.panelHeader}>Распределение по объектам</div>
						<div className={cls.chartBoxLg}>
							<Pie
								data={distribution}
								angleField="value"
								colorField="type"
								color={rtPalette}
								radius={0.9}
								innerRadius={0.65}
								label={false}
								legend={{ position: 'bottom' }}
							/>
						</div>
					</div>
				</div>
				<div className={cls["col-6"]}>
					<div className={cls.panel}>
						<div className={cls.panelHeader}>Тренд аномалий</div>
						<div className={cls.chartBoxLg}>
							<Line
								data={anomaliesTrend}
								xField="time"
								yField="value"
								color={rtPalette[1]}
								smooth
								lineStyle={{ lineWidth: 2 }}
							/>
						</div>
					</div>
				</div>
			</div>
		</div>
	)
}

