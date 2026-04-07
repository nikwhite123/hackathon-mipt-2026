import axiosClient from './axiosClient'
import type { OrgSettings } from '../constants/org'
import { backendEnabled } from './config'

export async function saveOrgSettings(payload: OrgSettings) {
	if (backendEnabled) {
		const { data } = await axiosClient.post('/org/settings', payload)
		return data
	}
	await new Promise((r) => setTimeout(r, 300))
	return { ok: true }
}

