import { useState, useEffect } from 'react';
import { threatService } from '../../api/threatService';
// import { IThreatPrediction } from '../../types/incident.types.ts';
import { useAppContext } from "../../hooks/useAppContext";

export const usePredictions = () => {
    const { predictions, setPredictions } = useAppContext();
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const fetchPredictions = async () => {
        try {
            setIsLoading(true);
            const data = await threatService.getPredictions();
            setPredictions(data);
            setError(null);
        } catch (err) {
            setError('Не удалось загрузить прогнозы атак');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchPredictions();
    }, []);

    return { predictions, isLoading, error, refetch: fetchPredictions };
};