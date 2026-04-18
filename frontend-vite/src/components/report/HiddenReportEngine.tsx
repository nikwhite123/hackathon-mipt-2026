/**
 * Off-screen clone of analytics + home sections for html2canvas/jsPDF export.
 */
import { lazy, Suspense } from "react"
import { Spin } from "antd"
import AnalyticsOverviewPanel from "../analytics/AnalyticsOverviewPanel"
import DashboardFiltersBar from "../dashboard/DashboardFiltersBar"

const HomePage = lazy(() => import("../../pages/HomePage"))

const fallback = (
  <div className="hidden-report-engine__section hidden-report-engine__fallback">
    <Spin size="large" />
  </div>
)

export function HiddenReportEngine() {
  return (
    <div id="hidden-report-engine" className="hidden-report-engine" aria-hidden>
      <div className="rt-content-outer">
        <div className="rt-content-inner hidden-report-engine__inner">
          <section
            id="pdf-export-analytics"
            className="hidden-report-engine__section"
            data-report-name="Аналитический отчет по угрозам"
          >
            <DashboardFiltersBar />
            <AnalyticsOverviewPanel />
          </section>
          <Suspense fallback={fallback}>
            <section
              id="pdf-export-dashboard"
              className="hidden-report-engine__section hidden-report-engine__section--spaced"
              data-report-name="Общая статистика защищенности (Главная)"
            >
              <HomePage />
            </section>
          </Suspense>
        </div>
      </div>
    </div>
  )
}
