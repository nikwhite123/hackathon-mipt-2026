import React from "react";
import { Card, Row, Col } from "antd";
import { Pie } from "@ant-design/plots";

const Dashboard: React.FC = () => {
  const threatData = [
    { type: "Сервер", value: 45, count: 12, color: "#6d28d9" },
    { type: "Приложение", value: 35, count: 9, color: "#10b981" },
    { type: "База данных", value: 20, count: 5, color: "#f59e0b" },
  ];

  const totalThreats = threatData.reduce((sum, item) => sum + item.count, 0);

  const pieConfig = {
    data: threatData,
    angleField: "value",
    colorField: "type",
    innerRadius: 0.72,   
    radius: 0.95,
    paddingAngle: 3,   
    legend: false,
    label: false,

    color: ({ type }: any) => {
      if (type === "Сервер") return "#6d28d9";
      if (type === "Приложение") return "#10b981";
      return "#f59e0b";
    },

    height: 260,
    width: 260,
    statistic: null,
  };

  return (
    <Card
      title="Распространение угроз"
      extra={<a href="#" style={{ color: "#6d28d9", fontWeight: 500 }}>Подробнее</a>}
      bordered={false}
      style={{ borderRadius: 12, marginTop: 20, maxWidth: 580 }}
      bodyStyle={{ padding: "24px 20px" }}
    >
      <Row gutter={24} align="middle">
        <Col flex="none" style={{ position: "relative" }}>
          <Pie {...pieConfig} />
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              textAlign: "center",
              pointerEvents: "none",
            }}
          >
            <div style={{ fontSize: "38px", fontWeight: 700, color: "#1f1f1f", lineHeight: 1 }}>
              {totalThreats}
            </div>
            <div style={{ fontSize: "13px", color: "#8c8c8c", marginTop: "6px" }}>
              Всего угроз
            </div>
          </div>
        </Col>
        <Col flex="auto" style={{ minWidth: 220 }}>
          {threatData.map((item, index) => (
            <div
              key={item.type}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: index === threatData.length - 1 ? 0 : 20,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div
                  style={{
                    width: 11,
                    height: 11,
                    borderRadius: "50%",
                    backgroundColor: item.color,
                  }}
                />
                <div>
                  <div style={{ fontWeight: 500, color: "#1f1f1f", fontSize: "14px" }}>
                    {item.type}
                  </div>
                  <div style={{ fontSize: "12.5px", color: "#8c8c8c" }}>
                    {item.count} угроз
                  </div>
                </div>
              </div>
              <div style={{ fontWeight: 600, fontSize: "15px" }}>{item.value}%</div>
            </div>
          ))}
        </Col>
      </Row>
    </Card>
  );
};

export default Dashboard;