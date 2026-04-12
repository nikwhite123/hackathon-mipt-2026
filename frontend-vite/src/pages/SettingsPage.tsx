import { Card, Col, Row, Select, InputNumber, Checkbox, Button, Space, Typography, message } from "antd"
import { useState } from "react"
import { saveOrgSettings } from "../api/orgService"
import {
	ENTERPRISE_TYPE_OPTIONS,
	REGION_OPTIONS,
	TECH_OPTIONS
} from "../constants/org"
import { useOrgStore } from "../store/orgStore"

export default function SettingsPage() {
	const { settings, update } = useOrgStore()
	const [loading, setLoading] = useState(false)

	const onSave = async () => {
		setLoading(true)
		try {
			await saveOrgSettings(settings)
			message.success("Настройки сохранены")
		} finally {
			setLoading(false)
		}
	}

	return (
		<Space direction="vertical" size={16} style={{ width: "100%" }}>
			<Typography.Title level={3}>Настройки организации</Typography.Title>
			<Card>
				<Row gutter={16}>
					<Col xs={24} md={6}>
						<label>Регион</label>
						<Select
							value={settings.region}
							onChange={(v) => update({ region: v })}
							options={REGION_OPTIONS}
							style={{ width: "100%" }}
						/>
					</Col>
					<Col xs={24} md={6}>
						<label>Тип предприятия</label>
						<Select
							value={settings.enterpriseType}
							onChange={(v) => update({ enterpriseType: v })}
							options={ENTERPRISE_TYPE_OPTIONS}
							style={{ width: "100%" }}
						/>
					</Col>
					<Col xs={24} md={6}>
						<label>Количество хостов</label>
						<InputNumber min={1} value={settings.hosts} onChange={(v) => update({ hosts: Number(v) })} style={{ width: "100%" }} />
					</Col>
					<Col xs={24} md={24} style={{ marginTop: 16 }}>
						<label>Технологии</label>
						<div style={{ marginTop: 8 }}>
							<Checkbox.Group
								options={TECH_OPTIONS}
								value={settings.technologies}
								onChange={(v) => update({ technologies: v as string[] })}
							/>
						</div>
					</Col>
				</Row>

				<Button type="primary" onClick={onSave} loading={loading} style={{ marginTop: 16 }}>
					Сохранить
				</Button>
			</Card>
		</Space>
	)
}
