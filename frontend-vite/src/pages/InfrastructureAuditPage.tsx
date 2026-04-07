import { Form, InputNumber, Select, Checkbox, Button, message } from "antd"
import { useState } from "react"
import { saveOrgSettings } from "../api/orgService"
import {
  ENTERPRISE_TYPE_OPTIONS,
  REGION_OPTIONS,
  TECH_OPTIONS
} from "../constants/org"
import { useOrgStore } from "../store/orgStore"
import Page from "../ui/Page"
import RTCard from "../ui/RTCard"
import style from "../Styles/HomePage.module.css"
import RadarPage from "./RadarPage.tsx";
import EarlyWarningPage from "./EarlyWarningPage.tsx";

export default function InfrastructureAuditPage() {
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const { settings, update } = useOrgStore()

  const onSubmit = async () => {
    const values = await form.validateFields()
    setLoading(true)
    try {
      await saveOrgSettings(values)
      message.success("Настройки сохранены")
    } finally {
      setLoading(false)
    }
  }

  return (
      <Page>
        <div className={style.infraAuditContainer}>
          <div className={style.infraAuditMainContent}>
            <RTCard>
              <div className={style.infraAuditLeftPanelContent}>
                <h2 className={style.infraAuditTitle}>Настройка инфраструктуры</h2>

                <Form
                    form={form}
                    layout="vertical"
                    onValuesChange={(changed) => update(changed)}
                    onFinish={onSubmit}
                    initialValues={settings}
                >
                  <div className={style.infraAuditFilters}>
                    <Form.Item label="Регион" name="region" rules={[{ required: true }]}>
                      <Select options={REGION_OPTIONS} />
                    </Form.Item>

                    <Form.Item label="Тип предприятия" name="enterpriseType" rules={[{ required: true }]}>
                      <Select options={ENTERPRISE_TYPE_OPTIONS} />
                    </Form.Item>

                    <Form.Item label="Количество хостов" name="hosts" rules={[{ required: true }]}>
                      <InputNumber min={1} style={{ width: "100%" }} />
                    </Form.Item>
                  </div>

                  <div className={style.infraAuditTechnologies}>
                    <Form.Item
                        label="Конструктор инфраструктуры"
                        name="technologies"
                        rules={[{ required: true }]}
                    >
                      <Checkbox.Group options={TECH_OPTIONS} />
                    </Form.Item>
                  </div>

                  <div className={style.infraAuditButtonContainer}>
                    <Button
                        type="primary"
                        htmlType="submit"
                        loading={loading}
                        size="large"
                        aria-label="Сохранить настройки организации"
                    >
                      Сохранить
                    </Button>
                  </div>
                </Form>
              </div>
            </RTCard>
          </div>
          <div className={style.infraAuditRightColumn}>
            <RadarPage />
            <EarlyWarningPage />
          </div>
        </div>
      </Page>
  )
}