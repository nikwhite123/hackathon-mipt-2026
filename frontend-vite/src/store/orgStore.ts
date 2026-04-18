/**
 * Editable org profile (region, industry, hosts, tech) and resolved organization code.
 */
import { create } from 'zustand'
import type { OrgSettings } from '../constants/org'
import { DEFAULT_ORG_SETTINGS } from '../constants/org'

export type { OrgSettings }

type OrgState = {
	settings: OrgSettings
  organizationCode: string
	update: (patch: Partial<OrgSettings>) => void
  setOrganizationCode: (organizationCode: string) => void
	reset: () => void
}

export const useOrgStore = create<OrgState>((set) => ({
	settings: DEFAULT_ORG_SETTINGS,
	organizationCode: '',
	update: (patch) => set((s) => ({ settings: { ...s.settings, ...patch } })),
	setOrganizationCode: (organizationCode) => set({ organizationCode }),
	reset: () => set({ settings: DEFAULT_ORG_SETTINGS, organizationCode: '' }),
}))
