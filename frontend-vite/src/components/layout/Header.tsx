import React, { useMemo } from "react";
import { Layout, Menu, Typography } from "antd";
import type { MenuProps } from "antd";
import {
  HomeOutlined,
  BookOutlined,
  LineChartOutlined,
  SecurityScanOutlined,
  ClusterOutlined,
} from "@ant-design/icons";
import { NavLink, useLocation, Link } from "react-router-dom";
import styles from "../../Styles/HomePage.module.css";

const { Header } = Layout;

const AppHeader: React.FC = () => {
  const { pathname } = useLocation();

  const selectedKey = useMemo(() => {
    if (pathname.startsWith("/infrastructure")) return "infrastructure";
    if (pathname.startsWith("/security-audit")) return "security-audit";
    if (pathname.startsWith("/analytics")) return "analytics";
    if (pathname.startsWith("/glossary")) return "glossary";
    return "dashboard";
  }, [pathname]);

  const items: MenuProps["items"] = [
    {
      key: "dashboard",
      icon: <HomeOutlined />,
      label: <NavLink to="/">Дашборд</NavLink>,
    },
    {
      key: "infrastructure",
      icon: <ClusterOutlined />,
      label: <NavLink to="/infrastructure">Инфраструктура</NavLink>,
    },
    {
      key: "security-audit",
      icon: <SecurityScanOutlined />,
      label: <NavLink to="/security-audit">Аудит</NavLink>,
    },
    {
      key: "analytics",
      icon: <LineChartOutlined />,
      label: <NavLink to="/analytics">Аналитика</NavLink>,
    },
    {
      key: "glossary",
      icon: <BookOutlined />,
      label: <NavLink to="/glossary">Глоссарий</NavLink>,
    },
  ];

  return (
    <Header className={styles.header}>
      <div className={styles.headerLeft}>
        <Link to="/" className={styles.brandlink}>
          <Typography.Text className={styles.brandtitle}>
            RT Infra Security
          </Typography.Text>
        </Link>
      </div>

      <div className={styles.headerCenter}>
        <Menu
          mode="horizontal"
          selectedKeys={[selectedKey]}
          items={items}
          style={{ borderBottom: "none",background: "transparent", display: "flex", justifyContent: "center", width: "100%", }}
        />
      </div>

      <div className={styles.headerRight} />
    </Header>
  );
};

export default AppHeader;