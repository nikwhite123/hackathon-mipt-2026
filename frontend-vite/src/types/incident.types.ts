export type TargetObjectType = 'server' | 'network_segment' | 'application' | 'database';

export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';

export interface IIncidentBase {
    id: string;
    type: string;
    severity: SeverityLevel;
    targetObject: string;
    targetType: TargetObjectType;
}

export interface IThreatPrediction extends IIncidentBase {
    probability: number;
    predictedTime: string;
    attackVector: string;
    vulnerabilityId: string;
    recommendationId: string;
}

export interface IVulnerability {
    id: string;
    title: string;
    description: string;
    isTechnical: boolean;
    riskScore: number;
}

export interface IProtectionStrategy {
    id: string;
    protocolName: string;
    steps: string[];
}