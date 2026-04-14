import React, {useMemo, useState} from "react";
import {Layout, Menu, Typography, Button, Space, Avatar} from "antd";
import type {MenuProps} from "antd";
import AuthModal from "../Auth/AuthModal.tsx";
import {
    HomeOutlined,
    BookOutlined,
    LineChartOutlined,
    SecurityScanOutlined,
    ClusterOutlined,
    UserOutlined,
} from "@ant-design/icons";
import {NavLink, useLocation, Link} from "react-router-dom";
import styles from "../../Styles/HomePage.module.css";


const {Header} = Layout;

const AppHeader: React.FC = () => {
    const {pathname} = useLocation();
    const [isAuthOpen, setIsAuthOpen] = useState(false);
    const [user, setUser] = useState<{ name: string } | null>(null);

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
            icon: <HomeOutlined/>,
            label: <NavLink to="/">Дашборд</NavLink>,
        },
        {
            key: "infrastructure",
            icon: <ClusterOutlined/>,
            label: <NavLink to="/infrastructure">Инфраструктура</NavLink>,
        },
        {
            key: "security-audit",
            icon: <SecurityScanOutlined/>,
            label: <NavLink to="/security-audit">Аудит</NavLink>,
        },
        {
            key: "analytics",
            icon: <LineChartOutlined/>,
            label: <NavLink to="/analytics">Аналитика</NavLink>,
        },
        {
            key: "glossary",
            icon: <BookOutlined/>,
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
                    style={{
                        borderBottom: "none",
                        background: "transparent",
                        display: "flex",
                        justifyContent: "center",
                        width: "100%",
                    }}
                />
            </div>

            <div className={styles.headerRight}>
                {user ? (
                    <Space>
                        <Avatar style={{backgroundColor: '#7733FF'}} icon={<UserOutlined/>}/>
                        <Typography.Text style={{color: '#fff'}}>{user.name}</Typography.Text>
                    </Space>
                ) : (
                    <Button
                        type="primary"
                        onClick={() => setIsAuthOpen(true)}
                        style={{backgroundColor: '#FF4F12', border: 'none'}}
                    >
                        Войти
                    </Button>
                )}
            </div>

            <AuthModal
                isOpen={isAuthOpen}
                onClose={() => setIsAuthOpen(false)}
                onSuccess={(name) => setUser({name})}
            />
        </Header>
    );
};

export default AppHeader;