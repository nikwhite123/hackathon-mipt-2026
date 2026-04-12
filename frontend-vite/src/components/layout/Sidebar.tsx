import React, { useMemo } from "react";
import { Layout, Menu } from "antd";
import type { MenuProps } from "antd";
import {
    HomeOutlined,
    BookOutlined,
    LineChartOutlined,
    SecurityScanOutlined,
    SettingOutlined,
    RadarChartOutlined,
    ClusterOutlined,
} from "@ant-design/icons";
import { NavLink, useLocation } from "react-router-dom";

import styles from "../../Styles/HomePage.module.css";

const { Sider } = Layout;

const Sidebar: React.FC = () => {
    const { pathname } = useLocation();

    const selectedKey = useMemo(() => {
        if (pathname.startsWith("/infrastructure")) return "infrastructure";
        if (pathname.startsWith("/early-warning")) return "early-warning";
        if (pathname.startsWith("/security-audit")) return "security-audit";
        if (pathname.startsWith("/radar")) return "radar";
        if (pathname.startsWith("/analytics")) return "analytics";
        if (pathname.startsWith("/glossary")) return "glossary";
        if (pathname.startsWith("/settings")) return "settings";
        return "dashboard";
    }, [pathname]);

    const items: MenuProps['items'] = [
        {
            key: 'dashboard',
            icon: <HomeOutlined />,
            label: <NavLink to="/">Дашборд</NavLink>
        },
        {
            key: 'infrastructure',
            icon: <ClusterOutlined />,
            label: <NavLink to="/infrastructure">Infrastructure Audit</NavLink>
        },
        {
            key: 'early-warning',
            icon: <SecurityScanOutlined />,
            label: <NavLink to="/early-warning">Раннее предупреждение</NavLink>
        },
        {
            key: 'security-audit',
            icon: <SecurityScanOutlined />,
            label: <NavLink to="/security-audit">Аудит защищенности</NavLink>
        },
        {
            key: 'radar',
            icon: <RadarChartOutlined />,
            label: <NavLink to="/radar">Radar</NavLink>
        },
        {
            key: 'analytics',
            icon: <LineChartOutlined />,
            label: <NavLink to="/analytics">Историческая аналитика</NavLink>
        },
        {
            key: 'glossary',
            icon: <BookOutlined />,
            label: <NavLink to="/glossary">Глоссарий</NavLink>
        },
        {
            key: 'settings',
            icon: <SettingOutlined />,
            label: <NavLink to="/settings">Настройки</NavLink>
        }
    ];

    return (
        <Sider width={250} className={styles.sider}>
            <div className={styles.logo}>RT Infra</div>

            <Menu
                theme="dark"
                mode="inline"
                selectedKeys={[selectedKey]}
                style={{ borderRight: 0 }}
                items={items}
            />
        </Sider>
    );
};

export default Sidebar;