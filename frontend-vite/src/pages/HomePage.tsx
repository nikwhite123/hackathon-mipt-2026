import React from "react";
import DashboardOverview from "../components/charts/DashboardOverview";
import Page from "../ui/Page";

const HomePage: React.FC = () => {
    return (

        <Page
            title="Дашборд"
            subtitle="Сводка по активности атак, аномалиям и распределению по объектам"
        >
            <DashboardOverview />
        </Page>
    );
};

export default HomePage;