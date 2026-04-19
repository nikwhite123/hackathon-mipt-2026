/**
 * Analytics hub: filters, ML-style predictions panel, overview and historical charts in tabs.
 */
import { Tabs } from "antd"
import AnalyticsOverviewPanel from "../components/analytics/AnalyticsOverviewPanel"
import PredictionsCollapsePanel from "../components/analytics/PredictionsCollapsePanel"
// import DashboardFiltersBar from "../components/dashboard/DashboardFiltersBar"
import HistoricalDashboard from "../components/layout/HistoricalDashboard"
import { useAuthStore } from "../store/authStore"
import Page from "../ui/Page"

export default function AnalyticsPage() {
	const { user } = useAuthStore()

	return (
		<Page>
			<div style={{ paddingTop: 34, paddingLeft: 34, paddingRight: 34 }}>
				{/*{user ? <DashboardFiltersBar /> : null}*/}
				{user ? <PredictionsCollapsePanel /> : null}
				<Tabs
					destroyInactiveTabPane
					items={[
						{
							key: "overview",
							label: "Обзор",
							children: <AnalyticsOverviewPanel />,
						},
						{
							key: "history",
							label: "История",
							children: <HistoricalDashboard hideFilters />,
						},
					]}
				/>
			</div>
		</Page>
	)
}
