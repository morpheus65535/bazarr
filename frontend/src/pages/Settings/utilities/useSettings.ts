import { createContext, useContext } from "react";

export const SettingsContext = createContext<Settings | null>(null);

export const useSettings = () => {
  const context = useContext(SettingsContext);

  return context;
};
