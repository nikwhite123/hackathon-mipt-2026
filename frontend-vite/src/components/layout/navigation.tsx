/**
 * Shared top-level navigation config used by the header and legacy sidebar.
 */
import type { ReactNode } from "react"
import type { MenuProps } from "antd"
import {
  BookOutlined,
  ClusterOutlined,
  HomeOutlined,
  LineChartOutlined,
  SecurityScanOutlined,
} from "@ant-design/icons"
import { NavLink } from "react-router-dom"

type NavigationItem = {
  key: string
  to: string
  label: string
  icon: ReactNode
}

const NAV_ITEMS: NavigationItem[] = [
  { key: "dashboard", to: "/", label: "Дашборд", icon: <HomeOutlined /> },
  { key: "infrastructure", to: "/infrastructure", label: "Инфраструктура", icon: <ClusterOutlined /> },
  { key: "security-audit", to: "/security-audit", label: "Аудит", icon: <SecurityScanOutlined /> },
  { key: "analytics", to: "/analytics", label: "Аналитика", icon: <LineChartOutlined /> },
  { key: "glossary", to: "/glossary", label: "Глоссарий", icon: <BookOutlined /> },
]

export function buildNavigationItems(): MenuProps["items"] {
  return NAV_ITEMS.map((item) => ({
    key: item.key,
    icon: item.icon,
    label: <NavLink to={item.to}>{item.label}</NavLink>,
  }))
}

export function getSelectedNavigationKey(pathname: string): string {
  const matched = NAV_ITEMS.find((item) => item.to !== "/" && pathname.startsWith(item.to))
  return matched?.key ?? "dashboard"
}
