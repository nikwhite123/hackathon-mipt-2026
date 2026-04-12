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

export interface IRecommendation {
    code: string;
    title: string;
    description: string;
    priority: number;
}

export interface IPredictionResponse {
    generated_at: string;
    risk_score: number;
    predicted_attack_time_window: string;
    predicted_target_object: string;
    predicted_attack_method: string;
    confidence: number;
    recommendations: IRecommendation[];
    rationale: string[];
}