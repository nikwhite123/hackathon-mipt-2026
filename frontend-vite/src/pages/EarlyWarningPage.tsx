import { Alert, Modal, Progress, Statistic, Typography, List, Badge, Button, Spin } from "antd"
import { useEffect, useMemo, useState } from "react"
import { fetchThreatForecast } from "../api/riskService"
import RTCard from "../ui/RTCard"
import style from "../Styles/HomePage.module.css"

import type { IPredictionResponse, IRecommendation } from "../types/incident.types"

export default function EarlyWarningPage() {
  const [visible, setVisible] = useState(false)
  const [threat, setThreat] = useState<IPredictionResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchThreatForecast()
      .then((data: IPredictionResponse) => setThreat(data))
      .catch((err) => console.error("Ошибка API:", err))
      .finally(() => setLoading(false))
  }, [])

  const stats = useMemo(() => ({
    probability: Math.round((threat?.confidence ?? 0) * 100),
    riskScore: Math.round((threat?.risk_score ?? 0) * 100),
    target: threat?.predicted_target_object?.toUpperCase() ?? "—",
    method: threat?.predicted_attack_method ?? "—",
    window: threat?.predicted_attack_time_window ?? "—"
  }), [threat])

  return (
    <div className={style.infraEarlyRow} style={{ marginTop: '16px' }}>
      <RTCard>
        <Spin spinning={loading}>
          <Statistic
            title="Уровень угрозы (Risk Score)"
            value={stats.riskScore}
            suffix="%"
            valueStyle={{ color: stats.riskScore > 60 ? '#FF4F12' : '#7733FF' }}
          />
          <div className={style.infraEarlyProgressContainer}>
            <Progress 
              percent={stats.riskScore} 
              status={stats.riskScore > 70 ? "exception" : "active"} 
              strokeColor={stats.riskScore > 60 ? '#FF4F12' : '#7733FF'}
            />
          </div>
          <Typography.Text type="secondary">Окно атаки: {stats.window}</Typography.Text>
        </Spin>
      </RTCard>

      <RTCard
        hoverable
        onClick={() => setVisible(true)}
      >
        <Spin spinning={loading}>
          <div className={style.infraEarlyContent}>
            <Alert
              message={`Цель: ${stats.target}`}
              description={`Метод: ${stats.method}`}
              type={stats.riskScore > 60 ? "error" : "warning"}
              showIcon
            />
            <div className={style.infraEarlyStatsGrid} style={{ marginTop: '12px' }}>
              <Statistic title="Точность прогноза" value={stats.probability} suffix="%" />
              <Button type="link" onClick={() => setVisible(true)} style={{ padding: 0 }}>
                Посмотреть меры защиты
              </Button>
            </div>
          </div>
        </Spin>
      </RTCard>

      <Modal
        open={visible}
        onCancel={() => setVisible(false)}
        footer={null}
        title="Рекомендации по противодействию"
        width={600}
      >
        <List
          itemLayout="horizontal"
          dataSource={threat?.recommendations ?? []}
          renderItem={(item: IRecommendation) => (
            <List.Item>
              <List.Item.Meta
                avatar={
                  <Badge 
                    count={item.priority} 
                    style={{ backgroundColor: item.priority === 1 ? '#FF4F12' : '#7733FF' }} 
                  />
                }
                title={item.title}
                description={item.description}
              />
            </List.Item>
          )}
        />
        {threat?.rationale && (
          <div style={{ marginTop: 16, padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
            <Typography.Text strong>Обоснование системы:</Typography.Text>
            <ul>
              {threat.rationale.map((r: string, i: number) => (
                <li key={i}><small>{r}</small></li>
              ))}
            </ul>
          </div>
        )}
      </Modal>
    </div>
  )
}