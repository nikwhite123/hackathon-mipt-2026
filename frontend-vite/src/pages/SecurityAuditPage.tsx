/**
 * Security audit: vulnerability-to-threat mapping table from `/vulnerabilities/map`.
 */
import { Table, Tag, Space, Typography, Badge } from "antd"
import { useEffect, useState } from "react"
import { threatService, type IVulnerabilityMapResponse } from "../api/threatService"
import { useAuthStore } from "../store/authStore"
import Page from "../ui/Page"
import RTCard from "../ui/RTCard"

const { Text } = Typography;
const RT_PURPLE = '#7733FF';
type MapItem = IVulnerabilityMapResponse["items"][number]
type VulnMatch = MapItem["matches"][number]

export default function SecurityAuditPage() {
  const { user } = useAuthStore()
  const [mapData, setMapData] = useState<MapItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setMapData([])
      setLoading(false)
      return
    }
    setLoading(true)
    threatService.getVulnerabilityMap()
      .then(data => {
        setMapData(data.items)
      })
      .catch(err => console.error("Ошибка карты:", err))
      .finally(() => setLoading(false));
  }, [user]);

  const columns = [
    { 
      title: "Ассет (Инфраструктура)", 
      dataIndex: "asset_name", 
      key: "asset_name",
      render: (name: string) => <Text strong>{name.toUpperCase()}</Text>
    },
    { 
      title: "Код уязвимости", 
      dataIndex: "vulnerability_code", 
      key: "vulnerability_code",
      render: (code: string) => <Tag color="volcano">{code}</Tag>
    },
    { 
      title: "Связанные угрозы", 
      key: "matches_count",
      render: (_: unknown, record: MapItem) => (
        <Space>
          <Badge count={record.matches.length} style={{ backgroundColor: RT_PURPLE }} />
          <Text type="secondary">угроз(ы) обнаружено</Text>
        </Space>
      )
    }
  ];

  return (
    <Page>
      <div style={{ paddingTop: '34px', paddingLeft: '34px', paddingRight: '34px' }}>
        <RTCard title="Карта соответствия уязвимостей и угроз">
          <Table
            loading={loading}
            dataSource={mapData}
            columns={columns}
            rowKey={(record) => record.asset_id + record.vulnerability_code}
            expandable={{
              expandedRowRender: (record) => (
                <div style={{ padding: '10px 24px', background: '#fdfdfd', border: '1px dashed #d9d9d9', borderRadius: '8px' }}>
                  <Text strong style={{ display: 'block', marginBottom: 8 }}>
                    Детальный анализ угроз для уязвимости {record.vulnerability_code}:
                  </Text>
                  {record.matches.map((m: VulnMatch, i: number) => (
                    <div key={i} style={{ marginBottom: 12 }}>
                      <Tag color="orange">{m.threat?.threat_id || `ID-${i}`}</Tag>
                      <Text strong>{m.threat?.name}</Text>
                      <p style={{ fontSize: '12px', color: '#666', margin: '4px 0 0 0' }}>{m.threat?.description}</p>
                      <p style={{ fontSize: '12px', color: '#666', margin: '4px 0 0 0' }}>
                        Совпадение: {Math.round((m.match_score ?? 0) * 100)}%. {m.reason}
                      </p>
                    </div>
                  ))}
                </div>
              ),
            }}
          />
        </RTCard>
      </div>
    </Page>
  )
}