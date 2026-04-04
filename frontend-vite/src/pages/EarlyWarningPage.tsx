import { Alert, Modal, Progress, Statistic, Typography } from "antd"
import { useEffect, useMemo, useState } from "react"
import { fetchThreatForecast, type ThreatForecast } from "../api/riskService"
import Page from "../ui/Page"
import RTCard from "../ui/RTCard"
import style from "../Styles/HomePage.module.css"

export default function EarlyWarningPage() {
  const [visible, setVisible] = useState(false)
  const [threat, setThreat] = useState<ThreatForecast | null>(null)

  useEffect(() => {
    fetchThreatForecast().then(setThreat).catch(() => {
      setThreat({
        id: "TST-001",
        target: "CRM-сервер",
        method: "Brute-force",
        probability: 0.72,
        etaMinutes: 43
      })
    })
  }, [])

  const progress = useMemo(() => Math.round((threat?.probability ?? 0) * 100), [threat])

  return (
      <Page>
        {/* ← Вот это главный контейнер для горизонтального расположения */}
        <div className={style.infraEarlyRow}>

          {/* Левая карточка */}
          <RTCard>
            <Statistic
                title="Ожидаемое время следующей атаки"
                value={threat?.etaMinutes ?? 0}
                suffix="мин"
            />
            <div className={style.infraEarlyProgressContainer}>
              <Progress percent={progress} status="active" />
            </div>
          </RTCard>

          {/* Правая карточка */}
          <RTCard
              hoverable
              onClick={() => setVisible(true)}
              role="button"
              aria-label="Открыть рекомендацию"
          >
            <div className={style.infraEarlyContent}>
              <Alert
                  message="Цель"
                  description={threat?.target ?? "—"}
                  type="warning"
                  showIcon
              />
              <div className={style.infraEarlyStatsGrid}>
                <div className={style.infraEarlyStatItem}>
                  <Statistic title="Вероятность" value={progress} suffix="%" />
                </div>
                <div className={style.infraEarlyStatItem}>
                  <Statistic title="Метод атаки" value={threat?.method ?? "—"} />
                </div>
              </div>
            </div>
          </RTCard>

        </div>

        <Modal
            open={visible}
            onCancel={() => setVisible(false)}
            onOk={() => setVisible(false)}
            okText="Принять меру"
            title="Рекомендация"
        >
          <Typography.Paragraph>
            Примените протокол защиты №1. Усильте политику паролей и заблокируйте подозрительные IP.
          </Typography.Paragraph>
        </Modal>
      </Page>
  )
}