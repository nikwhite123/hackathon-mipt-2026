/**
 * Auth-related DTOs aligned with `/auth/*` responses.
 */
export interface OrganizationOption {
  id: number
  name: string
  code: string | null
}

export interface AuthUser {
  id: number
  first_name: string
  last_name: string
  email: string
  organization_id: number
  organization_name: string
  organization_code: string | null
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

export interface RegisterPayload {
  first_name: string
  last_name: string
  email: string
  password: string
  organization_code: string
}

export interface LoginPayload {
  email: string
  password: string
}
