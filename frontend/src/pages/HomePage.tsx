import React from "react";
import styles from "../Styles/HomePage.module.css"
import Sidebar from "../components/layout/Sidebar";
import AppHeader from "../components/layout/Header";

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
                    <section className={styles.hero}>
                        <h1 className={styles.title}>
                            Интеллектуальная система кибербезопасности
                        </h1>
                        <p className={styles.subtitle}>
                            Анализируйте угрозы, предсказывайте атаки и защищайте инфраструктуру заранее
                        </p>
                        <button className={styles.button}>Начать анализ</button>
                    </section>

                    <section className={styles.features}>
                        <FeatureCard
                            title="Предиктивная аналитика"
                            description="Прогнозирование атак на основе времени, паттернов и поведения злоумышленников"
                        />
                        <FeatureCard
                            title="Диагностика уязвимостей"
                            description="Поиск слабых мест в инфраструктуре и рекомендации по их устранению"
                        />
                        <FeatureCard
                            title="Интеллектуальные рекомендации"
                            description="Готовые меры защиты на основе анализа и предсказаний системы"
                        />
                    </section>
                </div>
            </div>
        </div>
    );
};

interface FeatureCardProps {
    title: string;
    description: string;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ title, description }) => (
    <div className={styles.card}>
        <h3 className={styles.cardTitle}>{title}</h3>
        <p className={styles.cardText}>{description}</p>
    </div>
);

export default HomePage;