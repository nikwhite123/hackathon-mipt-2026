import React from "react";
import { Layout, Menu } from "antd";
import {
    HomeOutlined,
    LineChartOutlined,
    SecurityScanOutlined,
    SettingOutlined,
} from "@ant-design/icons";
import styles from "../../Styles/HomePage.module.css";

const { Sider } = Layout;

const Sidebar: React.FC = () => {
    return (
        <Sider width={250} className={styles.sider}>
            <div className={styles.logo}>My Dashboard</div>

            <Menu theme="dark" mode="inline" defaultSelectedKeys={["1"]} style={{ borderRight: 0 }}>
                <Menu.Item key="1" icon={<HomeOutlined />}>
                    Главная
                </Menu.Item>
                <Menu.Item key="2" icon={<LineChartOutlined />}>
                    Аналитика
                </Menu.Item>
                <Menu.Item key="3" icon={<SecurityScanOutlined />}>
                    Предсказания
                </Menu.Item>
                <Menu.Item key="4" icon={<SettingOutlined />}>
                    Настройки
                </Menu.Item>
            </Menu>
        </Sider>
    );
};

export default Sidebar;