import { useState } from "react"
import { Layout } from "antd"
import { Route, Routes, BrowserRouter } from "react-router-dom"
import HomePage from "./pages/HomePage"
import InfrastructureAuditPage from "./pages/InfrastructureAuditPage"
import EarlyWarningPage from "./pages/EarlyWarningPage"
import SecurityAuditPage from "./pages/SecurityAuditPage"
import RadarPage from "./pages/RadarPage"
import AnalyticsDashboardPage from "./pages/AnalyticsDashboardPage"
import NotFoundPage from "./pages/NotFoundPage"
// import Sidebar from "./components/layout/Sidebar"
import AppHeader from "./components/layout/Header"
import GlossaryPage from "./pages/GlossaryPage"
import SettingsPage from "./pages/SettingsPage"

function App() {
  const [isExporting, setIsExporting] = useState(false);
  return (
    <BrowserRouter>
      <Layout style={{ minHeight: "100vh" }}>
        <Layout>
          <AppHeader onStartExport={() => setIsExporting(true)} onEndExport={() => setIsExporting(false)} />
          <Layout.Content className="rt-content">
            <div className="rt-content-outer">
              <div className="rt-content-inner">
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/infrastructure" element={<InfrastructureAuditPage />} />
                  <Route path="/early-warning" element={<EarlyWarningPage />} />
                  <Route path="/security-audit" element={<SecurityAuditPage />} />
                  <Route path="/radar" element={<RadarPage />} />
                  <Route path="/analytics" element={<AnalyticsDashboardPage />} />
                  <Route path="/glossary" element={<GlossaryPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="*" element={<NotFoundPage />} />
                </Routes>
              </div>
            </div>
          </Layout.Content>
        </Layout>
        {isExporting && (
          <div
            id="hidden-report-engine"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '1600px',
              zIndex: -1000,
              visibility: 'visible',
              opacity: 1,
              background: '#fff',
              display: 'flex', 
              flexDirection: 'column'
            }}
          >
            <div id="full-analytics-report" style={{ width: '100%' }} data-report-name="Аналитический отчет по угрозам">
              <AnalyticsDashboardPage />
            </div>
            <div id="full-dashboard-report" style={{ width: '100%' }} data-report-name="Общая статистика защищенности (Главная)">
              <HomePage />
            </div>
          </div>
        )}
      </Layout>
    </BrowserRouter>
  )
}

export default App