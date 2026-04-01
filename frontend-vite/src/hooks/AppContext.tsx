import React, { createContext, useState } from "react";
import type { IThreatPrediction, IVulnerability } from "../types/incident.types";

export interface AppContextType {
  predictions: IThreatPrediction[];
  setPredictions: React.Dispatch<React.SetStateAction<IThreatPrediction[]>>;
  vulnerabilities: IVulnerability[];
  setVulnerabilities: React.Dispatch<React.SetStateAction<IVulnerability[]>>;
}

export const AppContext = createContext<AppContextType | null>(null);

export const AppProvider = ({ children }: any) => {
  const [predictions, setPredictions] = useState<IThreatPrediction[]>([]);
  const [vulnerabilities, setVulnerabilities] = useState<IVulnerability[]>([]);

  return (
    <AppContext.Provider
      value={{
        predictions,
        setPredictions,
        vulnerabilities,
        setVulnerabilities,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};