import React, {useState} from "react";
import styles from "../Styles/HomePage.module.css"
import Sidebar from "../components/layout/Sidebar";
import AppHeader from "../components/layout/Header";
import Dashboard from "../components/layout/Dashboard";
import Charts from "../components/layout/Сharts";
import Glossary from "../components/layout/Glossary.tsx";

const HomePage: React.FC = () => {
    const [activeMenu, setActiveMenu] = useState<"dashboard" | "glossary">("dashboard");

    const handleMenuClick = (key: string) => {
        if (key === "glossary") {
            setActiveMenu("glossary");
        } else {
            setActiveMenu("dashboard");
        }
    };

    return (
        <div className={styles.page}>
            <Sidebar onMenuClick={handleMenuClick} selectedKey={activeMenu}/>

            <div className={styles.main}>
                <AppHeader/>

                <div className={styles.content}>
                    {activeMenu === "dashboard" && (
                        <>
                            <Charts/>
                            <Dashboard/>
                        </>
                    )}

                    {activeMenu === "glossary" && <Glossary/>}
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