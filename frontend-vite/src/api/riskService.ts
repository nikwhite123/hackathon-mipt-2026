/**
 * Prediction API: builds `PredictRequest` from org settings and POSTs `/predict`.
 */
import axiosClient from './axiosClient'
import type { OrgSettings } from '../constants/org'
import type { IPredictionResponse } from '../types/incident.types'

type PredictRequestPayload = {
  /** Backend still expects the legacy key `organization_id`, but the value is the organization code. */
  organization_id: string
  region: string
  industry: string
  season: 'winter' | 'spring' | 'summer' | 'autumn'
  day_of_week: number
  hour: number
  asset_type: 'crm' | 'web_portal' | 'db_server' | 'file_server' | 'mail_gateway' | 'vpn_gateway' | 'workstation'
  has_external_access: boolean
  privileged_accounts_count: number
  known_vulnerabilities_count: number
  prefer_ml?: boolean
}

const REGION_TO_BACKEND: Record<string, string> = {
  MSK: 'Moscow',
  SPB: 'Saint Petersburg',
  SIB: 'Novosibirsk',
  FAR_EAST: 'Vladivostok',
  Moscow: 'Moscow',
  'Saint Petersburg': 'Saint Petersburg',
  Novosibirsk: 'Novosibirsk',
  Vladivostok: 'Vladivostok',
}

const INDUSTRY_TO_BACKEND: Record<string, string> = {
  Finance: 'finance',
  Telecom: 'telecom',
  Retail: 'retail',
  Gov: 'government',
  finance: 'finance',
  telecom: 'telecom',
  retail: 'retail',
  government: 'government',
}

function resolveRegion(region: string): string {
  return REGION_TO_BACKEND[region] ?? 'Moscow'
}

function resolveIndustry(industry: string): string {
  return INDUSTRY_TO_BACKEND[industry] ?? 'telecom'
}

function detectSeason(month: number): PredictRequestPayload['season'] {
  if ([12, 1, 2].includes(month)) return 'winter'
  if ([3, 4, 5].includes(month)) return 'spring'
  if ([6, 7, 8].includes(month)) return 'summer'
  return 'autumn'
}

export function buildPredictPayload(
  settings: OrgSettings,
  organizationCode: string,
  options?: { preferMl?: boolean },
): PredictRequestPayload {
  const now = new Date()
  const hosts = Math.max(1, Number(settings.hosts) || 1)
  const privileged_accounts_count = Math.max(1, Math.round(hosts / 40))
  const known_vulnerabilities_count = Math.max(
    1,
    Math.round(hosts / 100) + settings.technologies.length * 2,
  )
  return {
    organization_id: organizationCode,
    region: resolveRegion(String(settings.region)),
    industry: resolveIndustry(String(settings.enterpriseType)),
    season: detectSeason(now.getMonth() + 1),
    day_of_week: now.getDay() === 0 ? 7 : now.getDay(),
    hour: now.getHours(),
    asset_type: settings.technologies.includes('network')
      ? 'vpn_gateway'
      : settings.technologies.includes('sql')
        ? 'db_server'
        : settings.technologies.includes('web')
          ? 'web_portal'
          : 'workstation',
    has_external_access: settings.technologies.includes('web') || settings.technologies.includes('network'),
    privileged_accounts_count,
    known_vulnerabilities_count,
    ...(options?.preferMl ? { prefer_ml: true } : {}),
  }
}

export const fetchThreatForecast = async (
  settings: OrgSettings,
  organizationCode: string,
  options?: { preferMl?: boolean },
): Promise<IPredictionResponse> => {
  const payload = buildPredictPayload(settings, organizationCode, options)
  const { data } = await axiosClient.post('/predict', payload)
  return data
}
