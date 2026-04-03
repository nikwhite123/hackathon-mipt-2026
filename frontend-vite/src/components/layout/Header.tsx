import React from "react";
import { Layout, Avatar, Badge, Button, Typography } from "antd";
import { BellOutlined, UserOutlined } from "@ant-design/icons";
import { Link } from "react-router-dom";
import styles from "../../Styles/HomePage.module.css";

const { Header } = Layout;

const AppHeader: React.FC = () => {
  return (
    <Header className={styles.header} role="banner" aria-label="Верхняя панель">
      <div className={styles.headerleft}>
        <Link to="/" className={styles.brandlink}>
          <div className={styles.brandmark} aria-hidden="true" />
          <Typography.Text className={styles.brandtitle}>RT Infra Security</Typography.Text>
        </Link>
      </div>

      <div className={styles.headerright}>
        <Badge count={3} className={styles.badge}>
          <Button
            type="text"
            icon={<BellOutlined />}
            className={styles.iconbutton}
            aria-label="Уведомления"
          />
        </Badge>

        <Button type="text" className={styles.userblock} aria-label="Профиль пользователя">
          <Avatar icon={<UserOutlined />} size="small" />
          <span className={styles.username}>Ivanov</span>
        </Button>
      </div>
    </Header>
  );
};

export default AppHeader;