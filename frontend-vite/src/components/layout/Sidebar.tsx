import React from "react";
import { Layout, Menu } from "antd";
import {
    HomeOutlined,
    BookOutlined,
    LineChartOutlined,
    SecurityScanOutlined,
    SettingOutlined
} from "@ant-design/icons";

import styles from "../../Styles/HomePage.module.css";

const { Sider } = Layout;

interface SidebarProps {
    onMenuClick: (key: string) => void;
    selectedKey: string;
}

const Sidebar: React.FC<SidebarProps> = ({ onMenuClick, selectedKey }) => {
    return (
        <Sider width={250} className={styles.sider}>
            <div className={styles.logo}>My Dashboard</div>

            <Menu
                theme="dark"
                mode="inline"
                selectedKeys={[selectedKey]}
                style={{ borderRight: 0 }}
                onClick={({ key }) => onMenuClick(key)}
            >
                <Menu.Item key="dashboard" icon={<HomeOutlined />}>
                    Дашборд
                </Menu.Item>
                <Menu.Item key="glossary" icon={<BookOutlined />}>
                    Глоссарий
                </Menu.Item>
                <Menu.Item key="analytics" icon={<LineChartOutlined />}>
                    Аналитика
                </Menu.Item>
                <Menu.Item key="predictions" icon={<SecurityScanOutlined />}>
                    Предсказания
                </Menu.Item>
                <Menu.Item key="settings" icon={<SettingOutlined />}>
                    Настройки
                </Menu.Item>
            </Menu>
        </Sider>
    );
};

export default Sidebar;