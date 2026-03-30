import { useState, useEffect } from 'react';
import { threatService } from '../../api/threatService';
import { IVulnerability } from '../../types/incident.types';

export const useVulnerabilities = () => {
    const [vulnerabilities, setVulnerabilities] = useState<IVulnerability[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadData = async () => {
            try {
                const data = await threatService.getVulnerabilities();
                setVulnerabilities(data);
            } catch (err) {
                setError('Ошибка при аудите уязвимостей');
            } finally {
                setIsLoading(false);
            }
        };
        loadData();
    }, []);

    return { vulnerabilities, isLoading, error };
};