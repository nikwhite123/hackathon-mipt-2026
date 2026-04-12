export type Region = "MSK" | "SPB" | "SIB" | "FAR_EAST"

export type EnterpriseType = "Finance" | "Telecom" | "Retail" | "Gov"

export type OrgSettings = {
	region: Region
	enterpriseType: EnterpriseType
	hosts: number
	technologies: string[]
}

export const REGION_OPTIONS: { label: string; value: Region }[] = [
	{ label: "Москва", value: "MSK" },
	{ label: "Санкт‑Петербург", value: "SPB" },
	{ label: "Сибирь", value: "SIB" },
	{ label: "Дальний Восток", value: "FAR_EAST" }
]

export const ENTERPRISE_TYPE_OPTIONS: { label: string; value: EnterpriseType }[] = [
	{ label: "Финансы", value: "Finance" },
	{ label: "Телеком", value: "Telecom" },
	{ label: "Ритейл", value: "Retail" },
	{ label: "Госсектор", value: "Gov" }
]

export const TECH_OPTIONS: { label: string; value: string }[] = [
	{ label: "Docker", value: "docker" },
	{ label: "SQL", value: "sql" },
	{ label: "Web‑server", value: "web" },
	{ label: "Сеть", value: "network" }
]

export const REGIONS: readonly Region[] = ["MSK", "SPB", "SIB", "FAR_EAST"]

export const REGION_TIMEZONE_OFFSET_HOURS: Record<Region, number> = {
	MSK: 0,
	SPB: 0,
	SIB: 4,
	FAR_EAST: 7
}

export const DEFAULT_ORG_SETTINGS: OrgSettings = {
	region: "MSK",
	enterpriseType: "Telecom",
	hosts: 10,
	technologies: ["docker", "sql"]
}
