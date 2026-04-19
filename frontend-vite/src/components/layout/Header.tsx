/**
 * App header: primary nav, auth entry, PDF export trigger, and user menu.
 */
import React, { useState } from "react";
import { Layout, Menu, Typography, Button, Space, Avatar } from "antd";
import AuthModal from "../Auth/AuthModal.tsx";
import { generatePDFReport } from "../../utils/exportReport.ts";
import {
    UserOutlined,
    DownloadOutlined,
} from "@ant-design/icons";
import { FilterOutlined } from "@ant-design/icons";
import { useLocation, Link } from "react-router-dom";
import styles from "../../Styles/HomePage.module.css";
import { logout } from "../../api/authService";
import { useAuthStore } from "../../store/authStore";
import { useOrgStore } from "../../store/orgStore";
import { buildNavigationItems, getSelectedNavigationKey } from "./navigation.tsx";
import { useDashboardFiltersStore} from "../../store/dashboardFiltersStore.ts";

const { Header } = Layout

interface AppHeaderProps {
    onStartExport: () => void;
    onEndExport: () => void;
}

const AppHeader: React.FC<AppHeaderProps> = ({ onStartExport, onEndExport }) => {
    const { pathname } = useLocation();
    const [isAuthOpen, setIsAuthOpen] = useState(false);
    const { user, setUser } = useAuthStore();
    const setOrganizationCode = useOrgStore((s) => s.setOrganizationCode)
    const selectedKey = getSelectedNavigationKey(pathname)
    const { toggleFiltersPanel, filtersPanelExpanded } = useDashboardFiltersStore();
    const isAnalyticsPage = pathname === "/analytics" || pathname === "/" || pathname === "/infrastructure";

    const handleDownloadReport = () => {
        onStartExport();
        setTimeout(async () => {
            const elements = ["pdf-export-analytics", "pdf-export-dashboard"];

            try {
                await generatePDFReport(elements);
            } catch (e) {
                console.error("Ошибка при генерации:", e);
            } finally {
                onEndExport();
            }

        }, 2500);
    };

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
                    items={buildNavigationItems()}
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
                <Space>
                    {user && isAnalyticsPage && (
                        <Button
                            icon={<FilterOutlined />}
                            onClick={toggleFiltersPanel}
                            type={filtersPanelExpanded ? "primary" : "default"}
                            style={filtersPanelExpanded ? { backgroundColor: '#FF4F12', color: '#fff', borderColor: '#FF4F12' } : {}}
                        >
                            Фильтры
                        </Button>
                    )}
                    <Button
                        icon={<DownloadOutlined />}
                        onClick={handleDownloadReport}
                        style={{ borderColor: '#7733FF', backgroundColor: '#7733FF', color: '#fff' }}
                    >
                        Отчет PDF
                    </Button>
                    {user ? (
                        <Space>
                            <Avatar style={{ backgroundColor: '#7733FF' }} icon={<UserOutlined />} />
                            <Typography.Text style={{ color: '#fff' }}>
                                {user.first_name} {user.last_name}
                            </Typography.Text>
                            <Button
                                onClick={() => {
                                    logout()
                                }}
                            >
                                Выйти
                            </Button>
                        </Space>
                    ) : (
                        <Button
                            type="primary"
                            onClick={() => setIsAuthOpen(true)}
                            style={{ backgroundColor: '#FF4F12', border: 'none' }}
                        >
                            Войти
                        </Button>
                    )}
                </Space>
            </div>

            <AuthModal
                isOpen={isAuthOpen}
                onClose={() => setIsAuthOpen(false)}
                onSuccess={(currentUser) => {
                    setUser(currentUser)
                    setOrganizationCode(currentUser.organization_code ?? '')
                }}
            />
        </Header>
    );
};

export default AppHeader;