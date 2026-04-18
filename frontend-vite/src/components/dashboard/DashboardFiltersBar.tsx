/**
 * Dashboard filter controls bound to `dashboardFiltersStore` and `/stats/facets` options.
 */
import { DownOutlined, UpOutlined } from "@ant-design/icons"
import { Button, Col, Row, Select, Space, Typography } from "antd"
import { useEffect, useState } from "react"
import { fetchStatsFacets } from "../../api/analyticsService"
import { useAuthStore } from "../../store/authStore"
import { useDashboardFiltersStore, type DashboardFiltersState } from "../../store/dashboardFiltersStore"

const TOD_OPTIONS = [
	{ value: "", label: "Время суток (все)" },
	{ value: "night", label: "Ночь" },
	{ value: "morning", label: "Утро" },
	{ value: "afternoon", label: "День" },
	{ value: "evening", label: "Вечер" },
]

const SEASON_OPTIONS = [
	{ value: "", label: "Сезон (все)" },
	{ value: "winter", label: "Зима" },
	{ value: "spring", label: "Весна" },
	{ value: "summer", label: "Лето" },
	{ value: "autumn", label: "Осень" },
]

const METHOD_OPTIONS = [
	{ value: "", label: "Метод атаки (все)" },
	{ value: "malware", label: "Вредоносное ПО" },
	{ value: "phishing", label: "Фишинг" },
	{ value: "brute_force", label: "Подбор учётных данных" },
	{ value: "ransomware", label: "Шифровальщик" },
	{ value: "sql_injection", label: "SQL-инъекция" },
	{ value: "credential_stuffing", label: "Утечки учётных данных" },
]

const SUCCESS_OPTIONS = [
	{ value: "", label: "Успех атаки (все)" },
	{ value: "1", label: "Успешные" },
	{ value: "0", label: "Неуспешные" },
]

export default function DashboardFiltersBar() {
	const { user } = useAuthStore()
	const {
		dateFrom,
		dateTo,
		region,
		industry,
		success,
		timeOfDay,
		season,
		attackMethod,
		filtersPanelExpanded,
		setPatch,
		toggleFiltersPanel,
		reset,
	} = useDashboardFiltersStore()

	const [regions, setRegions] = useState<string[]>([])
	const [industries, setIndustries] = useState<string[]>([])

	useEffect(() => {
		if (!user) {
			setRegions([])
			setIndustries([])
			return
		}
		let cancelled = false
		fetchStatsFacets()
			.then((d) => {
				if (cancelled) return
				setRegions(d.regions ?? [])
				setIndustries(d.industries ?? [])
			})
			.catch(() => {
				if (!cancelled) {
					setRegions([])
					setIndustries([])
				}
			})
		return () => {
			cancelled = true
		}
	}, [user])

	return (
		<div style={{ marginBottom: 16, padding: "12px 16px", background: "#f8fafc", borderRadius: 8, border: "1px solid #e5e7eb" }}>
			<Row justify="space-between" align="middle" wrap={false} style={{ marginBottom: filtersPanelExpanded ? 8 : 0 }}>
				<Typography.Text strong>Фильтры выборки</Typography.Text>
				<Space size="small">
					<Button
						type="text"
						size="small"
						icon={filtersPanelExpanded ? <UpOutlined /> : <DownOutlined />}
						onClick={() => toggleFiltersPanel()}
						aria-expanded={filtersPanelExpanded}
					>
						{filtersPanelExpanded ? "Скрыть" : "Показать"}
					</Button>
					{filtersPanelExpanded ? (
						<Button size="small" onClick={() => reset()}>
							Сбросить
						</Button>
					) : null}
				</Space>
			</Row>
			{filtersPanelExpanded ? (
			<Row gutter={[12, 12]}>
				<Col xs={24} sm={12} md={6}>
					<Typography.Text type="secondary" style={{ display: "block", fontSize: 12 }}>
						Дата с
					</Typography.Text>
					<input
						type="date"
						value={dateFrom ?? ""}
						onChange={(e) => setPatch({ dateFrom: e.target.value || null })}
						style={{ width: "100%", height: 32, borderRadius: 6, border: "1px solid #d9d9d9", padding: "0 8px" }}
					/>
				</Col>
				<Col xs={24} sm={12} md={6}>
					<Typography.Text type="secondary" style={{ display: "block", fontSize: 12 }}>
						Дата по
					</Typography.Text>
					<input
						type="date"
						value={dateTo ?? ""}
						onChange={(e) => setPatch({ dateTo: e.target.value || null })}
						style={{ width: "100%", height: 32, borderRadius: 6, border: "1px solid #d9d9d9", padding: "0 8px" }}
					/>
				</Col>
				<Col xs={24} sm={12} md={6}>
					<Typography.Text type="secondary" style={{ display: "block", fontSize: 12 }}>
						Регион
					</Typography.Text>
					<Select
						allowClear
						placeholder="Все"
						value={region}
						onChange={(v) => setPatch({ region: v })}
						options={regions.map((r) => ({ value: r, label: r }))}
						style={{ width: "100%" }}
						showSearch
					/>
				</Col>
				<Col xs={24} sm={12} md={6}>
					<Typography.Text type="secondary" style={{ display: "block", fontSize: 12 }}>
						Отрасль
					</Typography.Text>
					<Select
						allowClear
						placeholder="Все"
						value={industry}
						onChange={(v) => setPatch({ industry: v })}
						options={industries.map((r) => ({ value: r, label: r }))}
						style={{ width: "100%" }}
						showSearch
					/>
				</Col>
				<Col xs={24} sm={12} md={6}>
					<Typography.Text type="secondary" style={{ display: "block", fontSize: 12 }}>
						Сезон
					</Typography.Text>
					<Select
						value={season || ""}
						onChange={(v) => setPatch({ season: (v || "") as DashboardFiltersState["season"] })}
						options={SEASON_OPTIONS}
						style={{ width: "100%" }}
					/>
				</Col>
				<Col xs={24} sm={12} md={6}>
					<Typography.Text type="secondary" style={{ display: "block", fontSize: 12 }}>
						Время суток
					</Typography.Text>
					<Select
						value={timeOfDay || ""}
						onChange={(v) => setPatch({ timeOfDay: (v || "") as DashboardFiltersState["timeOfDay"] })}
						options={TOD_OPTIONS}
						style={{ width: "100%" }}
					/>
				</Col>
				<Col xs={24} sm={12} md={6}>
					<Typography.Text type="secondary" style={{ display: "block", fontSize: 12 }}>
						Успех
					</Typography.Text>
					<Select
						value={success || ""}
						onChange={(v) => setPatch({ success: (v || "") as DashboardFiltersState["success"] })}
						options={SUCCESS_OPTIONS}
						style={{ width: "100%" }}
					/>
				</Col>
				<Col xs={24} sm={12} md={6}>
					<Typography.Text type="secondary" style={{ display: "block", fontSize: 12 }}>
						Метод (после классификации)
					</Typography.Text>
					<Select
						value={attackMethod || ""}
						onChange={(v) => setPatch({ attackMethod: v || "" })}
						options={METHOD_OPTIONS}
						style={{ width: "100%" }}
					/>
				</Col>
			</Row>
			) : null}
			{filtersPanelExpanded ? (
			<Space style={{ marginTop: 8 }}>
				<Typography.Text type="secondary" style={{ fontSize: 11 }}>
					Фильтры по дате, региону, отрасли, сезону, времени суток и успеху применяются в SQL; метод атаки — на сервере после
					соединения с реестром ФСТЭК.
				</Typography.Text>
			</Space>
			) : null}
		</div>
	)
}
