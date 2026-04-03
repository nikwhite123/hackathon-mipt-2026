import { create } from 'zustand'
import type { OrgSettings } from '../constants/org'
import { DEFAULT_ORG_SETTINGS } from '../constants/org'

export type { OrgSettings }

type OrgState = {
	settings: OrgSettings
	update: (patch: Partial<OrgSettings>) => void
	reset: () => void
}

export const useOrgStore = create<OrgState>((set) => ({
	settings: DEFAULT_ORG_SETTINGS,
	update: (patch) => set((s) => ({ settings: { ...s.settings, ...patch } })),
	reset: () => set({ settings: DEFAULT_ORG_SETTINGS })
}))
