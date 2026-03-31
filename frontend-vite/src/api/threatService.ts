import axiosClient from './axiosClient';
import { IThreatPrediction, IVulnerability, IProtectionStrategy } from '../types/incident.types';

export const threatService = {
    async getPredictions(): Promise<IThreatPrediction[]> {
        const { data } = await axiosClient.get<IThreatPrediction[]>('/predictions');
        return data;
    },

    async getVulnerabilities(): Promise<IVulnerability[]> {
        const { data } = await axiosClient.get<IVulnerability[]>('/vulnerabilities');
        return data;
    },

    async getProtectionStrategies(): Promise<IProtectionStrategy[]> {
        const { data } = await axiosClient.get<IProtectionStrategy[]>('/strategies');
        return data;
    }
};