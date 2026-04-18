/**
 * Home route: high-level dashboard overview inside the standard Page layout.
 */
import React from "react";
import DashboardOverview from "../components/charts/DashboardOverview";
import Page from "../ui/Page";

const HomePage: React.FC = () => {
    return (

        <Page>
            <DashboardOverview />
        </Page>
    );
};

export default HomePage;