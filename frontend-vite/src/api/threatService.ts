import axiosClient from './axiosClient'
import type { IProtectionStrategy, IThreatPrediction, IVulnerability } from '../types/incident.types'

export interface IThreat {
  threat_id: string;
  name: string;
  description: string;
  category: string;
  severity: "low" | "medium" | "high" | "critical";
  likely_targets: string[];
  common_methods: string[];
  source: string;
}

export interface IVulnerabilityMapResponse {
  total_assets: number;
  total_vulnerabilities: number;
  items: {
    asset_id: string;
    asset_name: string;
    vulnerability_code: string;
    matches: IThreat[];
  }[];
}

export const threatService = {
    async getPredictions(): Promise<IThreatPrediction[]> {
        const { data } = await axiosClient.get<IThreatPrediction[]>('/predictions');
        return data;
    },

    async getVulnerabilities(): Promise<IVulnerability[]> {
        const { data } = await axiosClient.get<IVulnerability[]>('/vulnerabilities');
        return data;
    },

async getVulnerabilityMap(vulnerabilities: any[] = []) {
    const payload = {
      vulnerabilities: vulnerabilities.length > 0 ? vulnerabilities : [
        {
          asset_id: "demo-1",
          asset_name: "Web Server",
          asset_type: "crm",
          vulnerability_code: "CVE-2023-1234",
          title: "SQL Injection",
          severity: "high",
          description: "Test vulnerability"
        }
      ]
    };

    const { data } = await axiosClient.post('/vulnerabilities/map', payload);
    return data;
  },

    async getProtectionStrategies(): Promise<IProtectionStrategy[]> {
        const { data } = await axiosClient.get<IProtectionStrategy[]>('/strategies');
        return data;
    },

    async getThreats(): Promise<{ total: number, items: IThreat[] }> {
    const { data } = await axiosClient.get('/threats');
    return data;
    },

    async getFullPrediction() {
        const { data } = await axiosClient.post('/predict', {});
        return data;
    },

    async getRecommendations() {
        const { data } = await axiosClient.post('/predict/recommendations', {});
        return data;
    }
}