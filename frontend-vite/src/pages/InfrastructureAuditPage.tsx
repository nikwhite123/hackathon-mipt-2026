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
import cls from "../Styles/rt.module.css"

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
      <RTCard>
        <Form
          form={form}
          layout="vertical"
          onValuesChange={(changed) => update(changed)}
          onFinish={onSubmit}
          initialValues={settings}
        >
          <div className={cls.filters}>
            <Form.Item label="Регион" name="region" rules={[{ required: true }]}>
              <Select options={REGION_OPTIONS} />
            </Form.Item>
            <Form.Item label="Тип предприятия" name="enterpriseType" rules={[{ required: true }]}>
              <Select options={ENTERPRISE_TYPE_OPTIONS} />
            </Form.Item>
            <Form.Item label="Количество хостов" name="hosts" rules={[{ required: true }]}>
              <InputNumber min={1} style={{ width: "100%" }} />
            </Form.Item>
            <div />
          </div>
          <Form.Item label="Конструктор инфраструктуры" name="technologies" rules={[{ required: true }]}>
            <Checkbox.Group options={TECH_OPTIONS} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} aria-label="Сохранить настройки организации">
            Сохранить
          </Button>
        </Form>
      </RTCard>
    </Page>
  )
}

