import { createContext, FunctionComponent, useContext } from "react";

const SettingsContext = createContext<Settings | null>(null);

export function useSettings() {
  const context = useContext(SettingsContext);

  return context;
}

type SettingsProviderProps = {
  value: Settings | null;
};

export const SettingsProvider: FunctionComponent<SettingsProviderProps> = ({
  value,
  children,
}) => {
  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};
