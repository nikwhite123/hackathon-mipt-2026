import React from "react";
import styles from "../Styles/HomePage.module.css"
import Sidebar from "../components/layout/Sidebar";
import AppHeader from "../components/layout/Header";
import Dashboard from "../components/layout/Dashboard";

const HomePage: React.FC = () => {
    return (
        <div className={styles.page}>
            <Sidebar />

            <div className={styles.main}>
                {/* <header className={styles.header}>
                    Моя интеллектуальная система кибербезопасности
                </header> */}
                <AppHeader />

                <div className={styles.content}>
                    <Dashboard />
                </div>
            </div>
        </div>
    );
};

// interface FeatureCardProps {
//     title: string;
//     description: string;
// }

// const FeatureCard: React.FC<FeatureCardProps> = ({ title, description }) => (
//     <div className={styles.card}>
//         <h3 className={styles.cardTitle}>{title}</h3>
//         <p className={styles.cardText}>{description}</p>
//     </div>
// );

export default HomePage;