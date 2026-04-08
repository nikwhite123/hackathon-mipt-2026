import axiosClient from './axiosClient'
// import { backendEnabled } from './config'

export type ThreatForecast = {
	id: string
	target: string
	method: string
	probability: number
	etaMinutes: number
}

const mockOrgData = {
  organization_id: "org-001",
  region: "Moscow",
  industry: "telecom",
  season: "winter",
  day_of_week: 1,
  hour: 23,
  asset_type: "crm",
  has_external_access: true,
  privileged_accounts_count: 12,
  known_vulnerabilities_count: 3
};

export const fetchThreatForecast = async () => {
  const { data } = await axiosClient.post('/predict', mockOrgData);
  return data;
};

// export async function fetchThreatForecast(): Promise<ThreatForecast> {
// 	if (backendEnabled) {
// 		const { data } = await axiosClient.get('/forecast/next')
// 		return data
// 	}
// 	await new Promise((r) => setTimeout(r, 200))
// 	return {
// 		id: 'TST-001',
// 		target: 'CRM-сервер',
// 		method: 'Brute-force',
// 		probability: 0.72,
// 		etaMinutes: 43
// 	}
// }

