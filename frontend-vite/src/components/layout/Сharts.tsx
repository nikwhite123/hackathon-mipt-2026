import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const data = [
  { date: "01.04", server: 0.7, application: 0.5, database: 0.2 },
  { date: "02.04", server: 0.6, application: 0.4, database: 0.3 },
  { date: "03.04", server: 0.8, application: 0.3, database: 0.4 },
  { date: "04.04", server: 0.9, application: 0.6, database: 0.3 },
  { date: "05.04", server: 0.5, application: 0.5, database: 0.4 },
  { date: "06.04", server: 0.7, application: 0.7, database: 0.6 },
  { date: "07.04", server: 0.9, application: 0.8, database: 0.5 },
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

const Charts: React.FC = () => {
  return (
    <div
      style={{
        width: "50%",
        height: 340,
        backgroundColor: "#fff",
        padding: 20,
        borderRadius: 12,
        boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 600 }}>Прогноз атак на объекты</h3>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "14px" }}>
          <span style={{ color: "#6d28d9", fontWeight: 600 }}>●</span>
          Вероятность атак
          <select style={{ border: "none", background: "transparent", fontWeight: 500, cursor: "pointer" }}>
            <option>Последняя неделя</option>
          </select>
        </div>
      </div>

      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
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

          <Area type="monotone" dataKey="server" stroke="#6d28d9" strokeWidth={3} fill="url(#colorServer)" dot={{ fill: "#fff", stroke: "#6d28d9", strokeWidth: 2, r: 4 }} activeDot={{ r: 6, fill: "#6d28d9", stroke: "#fff", strokeWidth: 2 }} />
          <Area type="monotone" dataKey="application" stroke="#10b981" strokeWidth={3} fill="url(#colorApplication)" dot={{ fill: "#fff", stroke: "#10b981", strokeWidth: 2, r: 4 }} activeDot={{ r: 6, fill: "#10b981", stroke: "#fff", strokeWidth: 2 }} />
          <Area type="monotone" dataKey="database" stroke="#f59e0b" strokeWidth={3} fill="url(#colorDatabase)" dot={{ fill: "#fff", stroke: "#f59e0b", strokeWidth: 2, r: 4 }} activeDot={{ r: 6, fill: "#f59e0b", stroke: "#fff", strokeWidth: 2 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Charts;