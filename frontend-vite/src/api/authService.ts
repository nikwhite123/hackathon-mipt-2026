/**
 * Auth API: login/register, current user, organization lookup; persists JWT via axiosClient helpers.
 */
import axiosClient, { clearClientSession, setAuthToken } from './axiosClient'
import type { LoginPayload, LoginResponse, OrganizationOption, RegisterPayload } from '../types/auth'

export async function fetchOrganizationByCode(code: string): Promise<OrganizationOption> {
  const trimmed = code.trim()
  const { data } = await axiosClient.get<OrganizationOption>('/auth/organization/by-code', {
    params: { code: trimmed },
  })
  return data
}

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await axiosClient.post<LoginResponse>('/auth/login', payload)
  setAuthToken(data.access_token)
  return data
}

export async function register(payload: RegisterPayload) {
  const { data } = await axiosClient.post('/auth/register', payload)
  return data
}

export async function fetchCurrentUser() {
  const { data } = await axiosClient.get<LoginResponse['user']>('/auth/me')
  return data
}

export function logout() {
  clearClientSession()
}
