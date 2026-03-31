import React from "react";
import { Card, Row, Col, Statistic } from "antd";
import { Area, Pie } from "@ant-design/plots";
import  styles from "../../Styles/HomePage.module.css";

const Dashboard: React.FC = () => {
  const areaData = [
    { time: "00:00", value: 3 },
    { time: "04:00", value: 7 },
    { time: "08:00", value: 15 },
    { time: "12:00", value: 10 },
    { time: "16:00", value: 18 },
    { time: "20:00", value: 8 },
  ];

  const pieData = [
    { type: "DDoS", value: 40 },
    { type: "Phishing", value: 25 },
    { type: "Malware", value: 20 },
    { type: "Brute Force", value: 15 },
  ];

  const total = pieData.reduce((acc, item) => acc + item.value, 0);

  const areaConfig = {
    data: areaData,
    xField: "time",
    yField: "value",
    smooth: true,

    color: "#1677ff",

    areaStyle: () => ({
      fill: "l(270) 0:rgba(22,119,255,0.4) 1:rgba(22,119,255,0)",
    }),

    tooltip: {
      showCrosshairs: true,
    },

    height: 300,
  };

  const pieConfig = {
    data: pieData,
    angleField: "value",
    colorField: "type",

    innerRadius: 0.7,
    radius: 0.9,

    legend: false,
    label: false,

    height: 300,
  };

  return (
    <div className={styles.dashboard}>
      <Row gutter={16} className={styles.dashboard_kpi}>
        <Col span={8}>
          <Card>
            <Statistic title="Всего атак" value={124} />
          </Card>
        </Col>

        <Col span={8}>
          <Card>
            <Statistic
              title="Критические"
              value={32}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>

        <Col span={8}>
          <Card>
            <Statistic
              title="Предотвращено"
              value={87}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={16}>
          <Card title="Атаки по времени" bordered={false}>
            <Area {...areaConfig} />
          </Card>
        </Col>

        <Col span={8}>
          <Card title="Типы атак" bordered={false}>
            <div className={styles.dashboard_pie_container}>

              <div className={styles.pie_wrapper}>
                <Pie {...pieConfig} />

                <div className={styles.pie_center}>
                  <div className={styles.pie_total}>{total}</div>
                  <div className={styles.pie_label}>атак</div>
                </div>
              </div>

              <div className={styles.pie_legend}>
                {pieData.map((item, index) => (
                  <div key={item.type} className={styles.legend_item}>
                    <div className={styles.legend_left}>
                      <div className={`${styles.legend_dot} ${styles[`legend_color_${index}`]}`} />
                      <span>{item.type}</span>
                    </div>

                    <span className={styles.legend_value}>{item.value}</span>
                  </div>
                ))}
              </div>

            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;