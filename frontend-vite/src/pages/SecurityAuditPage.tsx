import { Table, Tag } from "antd"
import Page from "../ui/Page"
import RTCard from "../ui/RTCard"

type Vulnerability = {
  id: string
  title: string
  severity: "low" | "medium" | "high" | "critical"
  component: string
  fstekCode: string
}

const data: Vulnerability[] = [
  { id: "V-001", title: "Слабый пароль администратора", severity: "high", component: "CRM", fstekCode: "УБИ.001" },
  { id: "V-002", title: "Неправильные ACL в сети", severity: "medium", component: "Сеть", fstekCode: "УБИ.013" },
  { id: "V-003", title: "Открытый SQL-порт", severity: "critical", component: "БД", fstekCode: "УБИ.021" }
]

export default function SecurityAuditPage() {
  return (
    <Page>
      <RTCard>
        <Table
          rowKey="id"
          dataSource={data}
          pagination={false}
          columns={[
            { title: "ID", dataIndex: "id", width: 100 },
            { title: "Описание", dataIndex: "title" },
            { title: "Компонент", dataIndex: "component", width: 160 },
            {
              title: "Код ФСТЭК",
              dataIndex: "fstekCode",
              width: 140,
              render: (v: string) => <Tag color="blue">{v}</Tag>
            },
            {
              title: "Критичность",
              dataIndex: "severity",
              width: 140,
              render: (s: Vulnerability["severity"]) => {
                const map: Record<string, string> = { low: "default", medium: "processing", high: "warning", critical: "error" }
                return <Tag color={map[s]}>{s}</Tag>
              }
            }
          ]}
        />
      </RTCard>
    </Page>
  )
}

