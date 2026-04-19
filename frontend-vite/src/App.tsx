/**
 * Root layout: lazy routes behind auth, landing when logged out, PDF export hook for reports.
 */
import {lazy, Suspense, useState} from "react"
import {Layout, Spin} from "antd"
import {Navigate, Route, Routes, BrowserRouter} from "react-router-dom"
import NotFoundPage from "./pages/NotFoundPage"
import AppHeader from "./components/layout/Header"
import {SessionProvider} from "./components/SessionProvider"
import {useAuthStore} from "./store/authStore"
import {HiddenReportEngine} from "./components/report/HiddenReportEngine"
import DashboardFiltersBar from "./components/dashboard/DashboardFiltersBar";
import {useDashboardFiltersStore} from "./store/dashboardFiltersStore";

const HomePage = lazy(() => import("./pages/HomePage"))
const InfrastructureAuditPage = lazy(() => import("./pages/InfrastructureAuditPage"))
const SecurityAuditPage = lazy(() => import("./pages/SecurityAuditPage"))
const AnalyticsPage = lazy(() => import("./pages/AnalyticsPage"))
const GlossaryPage = lazy(() => import("./pages/GlossaryPage"))
const LandingPage = lazy(() => import("./pages/LandingPage"))

const routeFallback = (
    <div style={{display: "flex", justifyContent: "center", padding: "48px 0"}}>
        <Spin size="large"/>
    </div>
)

/** Main shell with header, routes, and optional hidden report renderer for PDF export. */
function AuthenticatedApp() {
    const [isExporting, setIsExporting] = useState(false)
    const filtersPanelExpanded = useDashboardFiltersStore(s => s.filtersPanelExpanded);

    return (
        <Layout className="app-shell" style={{minHeight: "100vh"}}>
            <Layout>
                <AppHeader onStartExport={() => setIsExporting(true)} onEndExport={() => setIsExporting(false)}/>
                <div style={{
                    maxHeight: filtersPanelExpanded ? '1000px' : '0',
                    overflow: 'hidden',
                    transition: 'all 0.3s ease-in-out',
                    padding: filtersPanelExpanded ? '16px 24px 0' : '0 24px',
                    background: '#fff',
                    borderBottom: filtersPanelExpanded ? '1px solid #e5e7eb' : 'none'
                }}>
                    <DashboardFiltersBar/>
                </div>
                <Layout.Content className="rt-content">
                    <div className="rt-content-outer">
                        <div className="rt-content-inner">
                            <Suspense fallback={routeFallback}>
                                <Routes>
                                    <Route path="/" element={<HomePage/>}/>
                                    <Route path="/infrastructure" element={<InfrastructureAuditPage/>}/>
                                    <Route path="/early-warning" element={<Navigate to="/infrastructure" replace/>}/>
                                    <Route path="/security-audit" element={<SecurityAuditPage/>}/>
                                    <Route path="/radar" element={<Navigate to="/infrastructure" replace/>}/>
                                    <Route path="/analytics" element={<AnalyticsPage/>}/>
                                    <Route path="/glossary" element={<GlossaryPage/>}/>
                                    <Route path="/settings" element={<Navigate to="/infrastructure" replace/>}/>
                                    <Route path="*" element={<NotFoundPage/>}/>
                                </Routes>
                            </Suspense>
                        </div>
                    </div>
                </Layout.Content>
            </Layout>
            {isExporting ? <HiddenReportEngine/> : null}
        </Layout>
    )
}

/** Landing + redirect when anonymous; full app when `user` is set. */
function RoutedApp() {
    const user = useAuthStore((s) => s.user)

    if (!user) {
        return (
            <Suspense fallback={routeFallback}>
                <Routes>
                    <Route path="/" element={<LandingPage/>}/>
                    <Route path="*" element={<Navigate to="/" replace/>}/>
                </Routes>
            </Suspense>
        )
    }

    return <AuthenticatedApp/>
}

/** Router shell and session bootstrap (see SessionProvider). */
function App() {
    return (
        <BrowserRouter>
            <SessionProvider>
                <RoutedApp/>
            </SessionProvider>
        </BrowserRouter>
    )
}

export default App
