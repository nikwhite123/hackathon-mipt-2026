import { Select } from "antd"
import { Heatmap, Column } from "@ant-design/plots"
import { useEffect, useState } from "react"
import { fetchHeatmap, fetchDistribution } from "../api/analyticsService"
import Page from "../ui/Page"
import RTCard from "../ui/RTCard"
import { Grid, GridItem } from "../ui/Grid"
import cls from "../Styles/rt.module.css"

type Season = "all" | "winter" | "spring" | "summer" | "autumn"
type ThreatType = "all" | "network" | "app" | "credentials"

const seasons: { label: string; value: Season }[] = [
  { label: "Все сезоны", value: "all" },
  { label: "Зима", value: "winter" },
  { label: "Весна", value: "spring" },
  { label: "Лето", value: "summer" },
  { label: "Осень", value: "autumn" }
]

const threatTypes: { label: string; value: ThreatType }[] = [
  { label: "Все типы", value: "all" },
  { label: "Сеть", value: "network" },
  { label: "Приложения", value: "app" },
  { label: "Учетные данные", value: "credentials" }
]

function makeHeatmapData() {
  const days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
  const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, "0") + ":00")
  const data: { day: string; hour: string; value: number }[] = []
  days.forEach((d) => {
    hours.forEach((h) => {
      data.push({ day: d, hour: h, value: Math.round(Math.random() * 100) })
    })
  })
  return data
}

function makeDistributionData() {
  const categories = ["Серверы", "Сегменты сети", "БД", "Веб‑узлы", "Рабочие места"]
  return categories.map((c) => ({ category: c, count: Math.round(10 + Math.random() * 90) }))
}

export default function AnalyticsDashboardPage() {
  const [season, setSeason] = useState<Season>("all")
  const [tType, setTType] = useState<ThreatType>("all")

  const [heatmapData, setHeatmapData] = useState<any[]>([])
  const [distData, setDistData] = useState<any[]>([])

  useEffect(() => {
    const filters = { season, threatType: tType }
    fetchHeatmap(filters)
      .then((d) => setHeatmapData(d.length ? d : makeHeatmapData()))
      .catch(() => setHeatmapData(makeHeatmapData()))
    fetchDistribution(filters)
      .then((d) => setDistData(d.length ? d : makeDistributionData()))
      .catch(() => setDistData(makeDistributionData()))
  }, [season, tType])

  return (
    <Page title="Аналитика" subtitle="Активность атак и распределение по объектам">
      <div className={cls.stack16}>
      <RTCard>
        <div className={cls.filters}>
          <Select aria-label="Фильтр по сезону" value={season} onChange={setSeason} options={seasons} />
          <Select aria-label="Фильтр по типу угроз" value={tType} onChange={setTType} options={threatTypes} />
        </div>
      </RTCard>
      <Grid>
        <GridItem className={cls["col-8"]}>
          <RTCard title="Активность атак по времени (Heatmap)">
            <div className={cls.chartBox}>
              <Heatmap
                data={heatmapData}
                xField="hour"
                yField="day"
                colorField="value"
                autoFit
                shape="square"
                meta={{ value: { type: "linear", min: 0, max: 100 } }}
              />
            </div>
          </RTCard>
        </GridItem>
        <GridItem className={cls["col-4"]}>
          <RTCard title="Распределение атак по объектам воздействия">
            <div className={cls.chartBox}>
              <Column data={distData} xField="category" yField="count" autoFit />
            </div>
          </RTCard>
        </GridItem>
      </Grid>
      </div>
    </Page>
  )
}

