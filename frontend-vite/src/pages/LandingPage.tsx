/**
 * Public marketing landing with feature highlights and auth modal entry.
 */
import { useState } from "react"
import { BarChartOutlined, RadarChartOutlined, SafetyCertificateOutlined } from "@ant-design/icons"
import { Button, Col, Layout, Row, Typography } from "antd"
import AuthModal from "../components/Auth/AuthModal"
import { useAuthStore } from "../store/authStore"
import { useOrgStore } from "../store/orgStore"
import type { AuthUser } from "../types/auth"

const { Content } = Layout

const FEATURES = [
  {
    icon: <RadarChartOutlined className="landing-feature__icon" aria-hidden />,
    title: "Прогноз и контекст",
    text: "Оценка риска и сценариев с учётом инфраструктуры и времени.",
  },
  {
    icon: <BarChartOutlined className="landing-feature__icon" aria-hidden />,
    title: "Аналитика инцидентов",
    text: "Сводки и фильтры по данным вашей организации в БД.",
  },
  {
    icon: <SafetyCertificateOutlined className="landing-feature__icon" aria-hidden />,
    title: "Угрозы и уязвимости",
    text: "Каталог угроз и сопоставление с находками по активам.",
  },
] as const

export default function LandingPage() {
  const [authOpen, setAuthOpen] = useState(false)
  const { setUser } = useAuthStore()
  const setOrganizationCode = useOrgStore((s) => s.setOrganizationCode)

  const onAuthSuccess = (u: AuthUser) => {
    setUser(u)
    setOrganizationCode(u.organization_code ?? "")
    setAuthOpen(false)
  }

  return (
    <Layout className="landing-page">
      <Content className="landing-page__content">
        <div className="landing-page__glow" aria-hidden />

        <div className="landing-page__inner">
          <span className="landing-page__eyebrow">Платформа аналитики ИБ</span>

          <Typography.Title level={1} className="landing-page__title">
            RT Infra{" "}
            <span className="landing-page__title-accent">Security</span>
          </Typography.Title>

          <Typography.Paragraph className="landing-page__lead">
            Прогнозирование угроз, дашборды и отчёты — в одном интерфейсе. После входа данные изолируются по
            организации.
          </Typography.Paragraph>

          <Button type="primary" size="large" className="landing-page__cta" onClick={() => setAuthOpen(true)}>
            Войти в систему
          </Button>

          <Row gutter={[20, 20]} className="landing-page__features" justify="center">
            {FEATURES.map((f) => (
              <Col xs={24} sm={8} key={f.title}>
                <div className="landing-feature">
                  <div className="landing-feature__head">{f.icon}</div>
                  <Typography.Text className="landing-feature__title">{f.title}</Typography.Text>
                  <p className="landing-feature__text">{f.text}</p>
                </div>
              </Col>
            ))}
          </Row>

          <Typography.Text type="secondary" className="landing-page__footnote">
            Хакатон МФТИ · задача по предиктивной аналитике и защите инфраструктуры
          </Typography.Text>
        </div>

        <AuthModal isOpen={authOpen} onClose={() => setAuthOpen(false)} onSuccess={onAuthSuccess} />
      </Content>
    </Layout>
  )
}
