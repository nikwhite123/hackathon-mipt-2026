import React, { useState } from "react";
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
} from "recharts";
import { Card, Select, Typography, Space } from "antd";

const { Title } = Typography;
const { Option } = Select;

const objectDistribution = [
    { object: "Server", attacks: 45 },
    { object: "Application", attacks: 30 },
    { object: "Database", attacks: 25 },
];

const areaData = [
    { date: "01.04", server: 0.7, application: 0.5, database: 0.2 },
    { date: "02.04", server: 0.6, application: 0.4, database: 0.3 },
    { date: "03.04", server: 0.8, application: 0.3, database: 0.4 },
    { date: "04.04", server: 0.9, application: 0.6, database: 0.3 },
    { date: "05.04", server: 0.5, application: 0.5, database: 0.4 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div
                style={{
                    backgroundColor: "#fff",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                    border: "1px solid #e0e0e0",
                    fontSize: "14px",
                    fontWeight: 600,
                    color: "#333",
                }}
            >
                <div><strong>{label}</strong></div>
                {payload.map((p: any) => (
                    <div key={p.dataKey} style={{ color: p.stroke }}>
                        {p.dataKey.charAt(0).toUpperCase() + p.dataKey.slice(1)}: {(p.value * 100).toFixed(0)}%
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

const HistoricalDashboard: React.FC = () => {
    const [season, setSeason] = useState<string>("all");
    const [threatType, setThreatType] = useState<string>("all");

    return (
        <div style={{ padding: 24, maxWidth: 1200, margin: "0 auto" }}>
            <Title level={2}>Дашборд исторической аналитики</Title>

            <Space style={{ marginBottom: 24 }}>
                <Select value={season} onChange={setSeason} style={{ width: 160 }}>
                    <Option value="all">Все сезоны</Option>
                    <Option value="winter">Зима</Option>
                    <Option value="spring">Весна</Option>
                    <Option value="summer">Лето</Option>
                    <Option value="autumn">Осень</Option>
                </Select>

                <Select value={threatType} onChange={setThreatType} style={{ width: 200 }}>
                    <Option value="all">Все типы угроз</Option>
                    <Option value="malware">Вредоносное ПО</Option>
                    <Option value="phishing">Фишинг</Option>
                    <Option value="ddos">DDoS</Option>
                </Select>
            </Space>

            <Card style={{ marginBottom: 24, borderRadius: 12, padding: 20 }}>
                <Title level={4}>Прогноз атак на объекты</Title>
                <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={areaData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                        <defs>
                            <linearGradient id="colorServer" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#6d28d9" stopOpacity={0.6} />
                                <stop offset="95%" stopColor="#c4b5fd" stopOpacity={0.1} />
                            </linearGradient>
                            <linearGradient id="colorApplication" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.6} />
                                <stop offset="95%" stopColor="#a7f3d0" stopOpacity={0.1} />
                            </linearGradient>
                            <linearGradient id="colorDatabase" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.6} />
                                <stop offset="95%" stopColor="#fde68a" stopOpacity={0.1} />
                            </linearGradient>
                        </defs>

                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="date" tick={{ fontSize: 12, fill: "#666" }} tickLine={false} axisLine={false} />
                        <YAxis tick={{ fontSize: 12, fill: "#666" }} tickLine={false} axisLine={false} domain={[0, 1]} tickFormatter={(value) => `${value * 100}%`} />
                        <Tooltip content={<CustomTooltip />} />

                        <Area type="monotone" dataKey="server" stroke="#6d28d9" fill="url(#colorServer)" />
                        <Area type="monotone" dataKey="application" stroke="#10b981" fill="url(#colorApplication)" />
                        <Area type="monotone" dataKey="database" stroke="#f59e0b" fill="url(#colorDatabase)" />
                    </AreaChart>
                </ResponsiveContainer>
            </Card>

            <Card style={{ borderRadius: 12, padding: 20 }}>
                <Title level={4}>Распределение атак по объектам воздействия</Title>
                <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={objectDistribution}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="object" tick={{ fontSize: 12, fill: "#666" }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fontSize: 12, fill: "#666" }} axisLine={false} tickLine={false} />
                        <Tooltip />
                        <Bar dataKey="attacks" fill="#6d28d9" radius={[6, 6, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </Card>
        </div>
    );
};

export default HistoricalDashboard;