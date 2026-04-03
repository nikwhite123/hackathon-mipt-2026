import { Layout } from "antd"
import { Route, Routes, BrowserRouter } from "react-router-dom"
import HomePage from "./pages/HomePage"
import InfrastructureAuditPage from "./pages/InfrastructureAuditPage"
import EarlyWarningPage from "./pages/EarlyWarningPage"
import SecurityAuditPage from "./pages/SecurityAuditPage"
import RadarPage from "./pages/RadarPage"
import AnalyticsDashboardPage from "./pages/AnalyticsDashboardPage"
import NotFoundPage from "./pages/NotFoundPage"
import Sidebar from "./components/layout/Sidebar"
import AppHeader from "./components/layout/Header"
import GlossaryPage from "./pages/GlossaryPage"
import SettingsPage from "./pages/SettingsPage"

function App() {
  return (
    <BrowserRouter>
      <Layout style={{ minHeight: "100vh" }}>
        <Sidebar />
        <Layout>
          <AppHeader />
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
      </Layout>
    </BrowserRouter>
  )
}

export default App