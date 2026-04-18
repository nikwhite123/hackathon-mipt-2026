/**
 * Collapsible panel that loads and displays full `/predict` response for the signed-in org.
 */
import { Button, Collapse, Descriptions, List, Spin, Typography, Alert, Space } from "antd"
import { useState } from "react"
import { useThreatForecast } from "../../hooks/useThreatForecast"
import { useAuthStore } from "../../store/authStore"
import { useOrgStore } from "../../store/orgStore"
import type { IRecommendation } from "../../types/incident.types"

export default function PredictionsCollapsePanel() {
	const { user } = useAuthStore()
	const { organizationCode } = useOrgStore()
	const [activeKeys, setActiveKeys] = useState<string[]>([])
	const [preferMl, setPreferMl] = useState(false)

	const forecastOpen = activeKeys.includes("forecast")
	const { data, loading, error } = useThreatForecast({ enabled: forecastOpen && !!user, preferMl })

	if (!user) return null

	return (
		<Collapse
			style={{ marginBottom: 16 }}
			activeKey={activeKeys}
			onChange={(keys) => setActiveKeys(Array.isArray(keys) ? keys : [keys])}
			items={[
				{
					key: "forecast",
					label: "Актуальный прогноз по настройкам инфраструктуры",
					children: (
						<div>
							{!organizationCode ? (
								<Alert type="warning" message="Укажите код организации (войдите заново при необходимости)." showIcon />
							) : null}
							{error ? <Alert type="error" message={error} showIcon style={{ marginBottom: 12 }} /> : null}
							<Space style={{ marginBottom: 8 }} wrap>
								<Button type={preferMl ? "default" : "primary"} onClick={() => setPreferMl(false)}>
									Эвристический прогноз
								</Button>
								<Button type={preferMl ? "primary" : "default"} onClick={() => setPreferMl(true)}>
									Получить ML-прогноз
								</Button>
							</Space>
							<Typography.Text type="secondary" style={{ display: "block", marginBottom: 12, fontSize: 12 }}>
								ML-режим меняет только метод и цель атаки. Risk score и окно атаки остаются эвристическими.
							</Typography.Text>
							<Space align="center" style={{ marginBottom: 12 }} wrap>
								<Typography.Text type="secondary" style={{ fontSize: 12 }}>
									{preferMl ? "Сейчас отображается ML-прогноз для метода и цели атаки." : "Сейчас отображается эвристический прогноз."}
								</Typography.Text>
							</Space>
							<Spin spinning={loading}>
								{data ? (
									<>
										<Descriptions bordered size="small" column={1} style={{ marginBottom: 16 }}>
											<Descriptions.Item label="Risk score">{Math.round((data.risk_score ?? 0) * 100)}%</Descriptions.Item>
											<Descriptions.Item label="Уверенность">{Math.round((data.confidence ?? 0) * 100)}%</Descriptions.Item>
											<Descriptions.Item label="Окно атаки">{data.predicted_attack_time_window}</Descriptions.Item>
											<Descriptions.Item label="Цель">{data.predicted_target_object}</Descriptions.Item>
											<Descriptions.Item label="Метод">{data.predicted_attack_method}</Descriptions.Item>
										</Descriptions>
										<Typography.Title level={5}>Обоснование</Typography.Title>
										<List
											size="small"
											dataSource={data.rationale ?? []}
											renderItem={(item: string) => <List.Item>{item}</List.Item>}
										/>
										<Typography.Title level={5} style={{ marginTop: 16 }}>
											Рекомендации
										</Typography.Title>
										<List
											size="small"
											dataSource={data.recommendations ?? []}
											renderItem={(item: IRecommendation) => (
												<List.Item>
													<Typography.Text strong>
														{item.priority}. {item.title}
													</Typography.Text>
													<div>{item.description}</div>
												</List.Item>
											)}
										/>
									</>
								) : loading ? null : (
									<Typography.Text type="secondary">
										Данные появятся после раскрытия блока. При необходимости сохраните настройки на странице инфраструктуры.
									</Typography.Text>
								)}
							</Spin>
						</div>
					),
				},
			]}
		/>
	)
}
