import { Progress, Statistic, Typography } from "antd"
import { useEffect, useMemo, useState } from "react"
import type { Region } from "../constants/org"
import { REGIONS, REGION_TIMEZONE_OFFSET_HOURS } from "../constants/org"
import { useOrgStore } from "../store/orgStore"
import cn from "../utils/cn"
import Page from "../ui/Page"
import RTCard from "../ui/RTCard"
import { Grid, GridItem } from "../ui/Grid"
import cls from "../Styles/rt.module.css"

export default function RadarPage() {
  const { settings, update } = useOrgStore()
  const [region, setRegion] = useState<Region>(settings.region)
  const [risk, setRisk] = useState(0.35)
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const regionalTime = useMemo(() => {
    const d = new Date(now)
    d.setHours(d.getUTCHours() + 3 + REGION_TIMEZONE_OFFSET_HOURS[region])
    return d.toLocaleTimeString("ru-RU", { hour12: false })
  }, [now, region])

  useEffect(() => {
    const t = setInterval(() => {
      setRisk((r) => {
        const n = Math.max(0, Math.min(1, r + (Math.random() - 0.5) * 0.08))
        return Number(n.toFixed(2))
      })
    }, 2000)
    return () => clearInterval(t)
  }, [])

  return (
    <Page>
      <Grid>
        <GridItem className={cls["col-4"]}>
          <RTCard>
            <Statistic title="Текущее региональное время" value={regionalTime} />
            <div className={cn(cls.pillRow, cls.mt12)}>
              {REGIONS.map((r) => (
                <button
                  key={r}
                  onClick={() => {
                    setRegion(r)
                    update({ region: r })
                  }}
                  className={cls.pillButton}
                >
                  {r}
                </button>
              ))}
            </div>
          </RTCard>
        </GridItem>
        <GridItem className={cls["col-4"]}>
          <RTCard>
            <Typography.Text>Индекс риска</Typography.Text>
            <div className={cls.mt12}>
              <Progress type="dashboard" percent={Math.round(risk * 100)} />
            </div>
          </RTCard>
        </GridItem>
        <GridItem className={cls["col-4"]}>
          <RTCard>
            {risk > 0.7 ? (
              <>
                <Typography.Title level={5}>Высокий риск</Typography.Title>
                <Typography.Paragraph>Код угрозы: УБИ.021 — SQL Injection</Typography.Paragraph>
              </>
            ) : (
              <>
                <Typography.Title level={5}>Низкий/умеренный риск</Typography.Title>
                <Typography.Paragraph>Система мониторинга активна. Аномалий не обнаружено.</Typography.Paragraph>
              </>
            )}
          </RTCard>
        </GridItem>
      </Grid>
    </Page>
  )
}

