import { Alert, Modal, Progress, Statistic, Typography } from "antd"
import { useEffect, useMemo, useState } from "react"
import { fetchThreatForecast, type ThreatForecast } from "../api/riskService"
import Page from "../ui/Page"
import RTCard from "../ui/RTCard"
import { Grid, GridItem } from "../ui/Grid"
import cn from "../utils/cn"
import cls from "../Styles/rt.module.css"

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
      <Grid>
        <GridItem className={cls["col-4"]}>
          <RTCard>
            <Statistic title="Ожидаемое время следующей атаки" value={threat?.etaMinutes ?? 0} suffix="мин" />
            <div className={cn(cls.stack16, cls.mt12)}>
              <Progress percent={progress} status="active" />
            </div>
          </RTCard>
        </GridItem>
        <GridItem className={cls["col-8"]}>
          <RTCard hoverable onClick={() => setVisible(true)} role="button" aria-label="Открыть рекомендацию" className={cls.clickable}>
            <div className={cls.stack16}>
              <Alert message="Цель" description={threat?.target ?? "—"} type="warning" showIcon />
              <div className={cls.grid}>
                <div className={cls["col-6"]}>
                  <Statistic title="Вероятность" value={progress} suffix="%" />
                </div>
                <div className={cls["col-6"]}>
                  <Statistic title="Метод атаки" value={threat?.method ?? "—"} />
                </div>
              </div>
            </div>
          </RTCard>
        </GridItem>
      </Grid>

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

