/**
 * Loads JWT user and org settings on mount; gates children until session is ready.
 */
import { Spin } from "antd"
import { useEffect, useState, type ReactNode } from "react"
import { fetchCurrentUser, logout } from "../api/authService"
import { clearClientSession, getAuthToken } from "../api/axiosClient"
import { fetchOrgSettings } from "../api/orgService"
import type { EnterpriseType, Region } from "../constants/org"
import { useAuthStore } from "../store/authStore"
import { useOrgStore } from "../store/orgStore"

export function SessionProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false)
  const { user, setUser } = useAuthStore()
  const { setOrganizationCode, update } = useOrgStore()

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      if (!getAuthToken()) {
        clearClientSession()
        if (!cancelled) setReady(true)
        return
      }
      try {
        const currentUser = await fetchCurrentUser()
        if (cancelled) return
        setUser(currentUser)
        setOrganizationCode(currentUser.organization_code ?? "")
      } catch {
        if (!cancelled) {
          logout()
        }
      } finally {
        if (!cancelled) setReady(true)
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [setUser, setOrganizationCode])

  useEffect(() => {
    if (!user?.id) return
    let cancelled = false
    setOrganizationCode(user.organization_code ?? "")
    fetchOrgSettings()
      .then((orgSettings) => {
        if (cancelled || !orgSettings) return
        update({
          region: orgSettings.region as Region,
          enterpriseType: orgSettings.industry as EnterpriseType,
          hosts: orgSettings.host_count,
          technologies: orgSettings.technologies ?? [],
        })
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          console.warn("Failed to load organization settings", error)
        }
      })
    return () => {
      cancelled = true
    }
  }, [user?.id, user?.organization_code, setOrganizationCode, update])

  if (!ready) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 120 }}>
        <Spin size="large" />
      </div>
    )
  }

  return <>{children}</>
}
