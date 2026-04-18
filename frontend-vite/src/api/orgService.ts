/**
 * Organization infrastructure settings: `GET/POST /org/settings`.
 */
import axiosClient from './axiosClient'
import type { OrgSettings } from '../constants/org'

export async function saveOrgSettings(payload: OrgSettings) {
  const { data } = await axiosClient.post('/org/settings', {
    region: payload.region,
    industry: payload.enterpriseType,
    host_count: payload.hosts,
    technologies: payload.technologies,
  })
  return data
}

export async function fetchOrgSettings() {
  const { data } = await axiosClient.get('/org/settings')
  return data
}
