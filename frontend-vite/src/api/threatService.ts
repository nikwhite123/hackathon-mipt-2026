/**
 * Threat catalog (`GET /threats`) and vulnerability-to-threat mapping (`POST /vulnerabilities/map`).
 */
import axiosClient from './axiosClient'

export interface IThreat {
  threat_id: string
  name: string
  description: string
  category: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  likely_targets: string[]
  common_methods: string[]
  source: string
}

export interface IVulnerabilityMapResponse {
  total_assets: number
  total_vulnerabilities: number
  items: {
    asset_id: string
    asset_name: string
    vulnerability_code: string
    matches: {
      threat: IThreat
      match_score: number
      reason: string
      recommended_actions: {
        code: string
        title: string
        description: string
        priority: number
      }[]
    }[]
  }[]
}

export const threatService = {
  async getVulnerabilityMap(
    vulnerabilities: Array<Record<string, unknown>> = [],
  ): Promise<IVulnerabilityMapResponse> {
    const payload = {
      vulnerabilities:
        vulnerabilities.length > 0
          ? vulnerabilities
          : [
              {
                asset_id: 'demo-1',
                asset_name: 'Web Server',
                asset_type: 'crm',
                vulnerability_code: 'CVE-2023-1234',
                title: 'SQL Injection',
                severity: 'high',
                description: 'Test vulnerability',
              },
            ],
    }

    const { data } = await axiosClient.post<IVulnerabilityMapResponse>('/vulnerabilities/map', payload)
    return data
  },

  async getThreats(): Promise<{ total: number; items: IThreat[] }> {
    const { data } = await axiosClient.get('/threats')
    return data
  },
}
