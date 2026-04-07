import { Heatmap, Column } from "@ant-design/plots"
import { useEffect, useState } from "react"
import { fetchStats } from "../api/analyticsService"
import Page from "../ui/Page"
import RTCard from "../ui/RTCard"
import { Grid, GridItem } from "../ui/Grid"
import cls from "../Styles/rt.module.css"

// Брендовые цвета Ростелекома
const RT_ORANGE = '#FF4F12';
const RT_PURPLE = '#7733FF';
const RT_DARK = '#101828';

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

export default function AnalyticsDashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [distData, setDistData] = useState<{category: string, count: number}[]>([]);

  useEffect(() => {
    fetchStats().then((data) => {
      setStats(data);
      if (data && data.risk_distribution) {
        const formattedDist = Object.entries(data.risk_distribution).map(([key, value]) => ({
          category: key.toUpperCase(),
          count: value as number
        }));
        setDistData(formattedDist);
      }
    }).catch(err => console.error("Ошибка загрузки статистики:", err));
  }, []);

  return (
      <Page>
        {/* Добавляем контейнер с padding-top, чтобы отодвинуть контент от Header */}
        <div style={{ paddingTop: '24px' }}>
          <div className={cls.stack16}>
            <Grid>
              <GridItem className={cls["col-4"]}>
                <RTCard title="Всего инцидентов">
                  {/* Используем фиолетовый для общего счетчика */}
                  <h2 style={{ fontSize: '2.5rem', margin: 0, color: RT_PURPLE }}>
                    {stats?.total_incidents || 0}
                  </h2>
                </RTCard>
              </GridItem>
              <GridItem className={cls["col-4"]}>
                <RTCard title="Топ метод">
                  {/* Используем оранжевый для акцента на методе */}
                  <h2 style={{ color: RT_ORANGE, margin: 0, fontWeight: 'bold' }}>
                    {stats?.top_attack_method?.toUpperCase() || '—'}
                  </h2>
                </RTCard>
              </GridItem>
              <GridItem className={cls["col-4"]}>
                <RTCard title="Главная цель">
                  <h2 style={{ color: RT_DARK, margin: 0 }}>
                    {stats?.top_target_object?.toUpperCase() || '—'}
                  </h2>
                </RTCard>
              </GridItem>
            </Grid>

            <Grid>
              <GridItem className={cls["col-8"]}>
                <RTCard title="Активность атак (Карта интенсивности)">
                  <div style={{ height: 350 }}>
                    <Heatmap
                        data={makeHeatmapData()}
                        xField="hour"
                        yField="day"
                        colorField="value"
                        autoFit
                        // Градиент от белого к фиолетовому (стиль РТ)
                        color={['#ffffff', RT_PURPLE]}
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
                        // Оранжевый для критических, фиолетовый для остальных
                        color={({ category }: { category: string }) => {
                          return (category === 'CRITICAL' || category === 'HIGH')
                              ? RT_ORANGE
                              : RT_PURPLE;
                        }}
                        columnStyle={{
                          radius: [4, 4, 0, 0] // Слегка скругляем верхушки
                        }}
                    />
                  </div>
                </RTCard>
              </GridItem>
            </Grid>
          </div>
        </div>
      </Page>
  )
}