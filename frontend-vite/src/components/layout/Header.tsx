import React from "react";
import { Layout, Avatar, Badge, Button } from "antd";
import { BellOutlined, UserOutlined } from "@ant-design/icons";
import styles from "../../Styles/HomePage.module.css";

const { Header } = Layout;

const AppHeader: React.FC = () => {
  return (
    <Header className={styles.header}>
      <div className={styles.headerleft}>
        Cyber Security Dashboard
      </div>

      <div className={styles.headerright}>
        <Badge count={7}>
          <Button
            shape="circle"
            icon={<BellOutlined />}
            className={styles.iconbutton}
          />
        </Badge>

        <Button type="text" className={styles.userblock}>
          <Avatar icon={<UserOutlined />} />
          <span className={styles.username}>Ivanov</span>
        </Button>
      </div>
    </Header>
  );
};

export default AppHeader;