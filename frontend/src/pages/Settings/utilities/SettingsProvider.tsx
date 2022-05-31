import { createContext, FunctionComponent, useContext } from "react";

const SettingsContext = createContext<Settings | null>(null);

export function useSettings() {
  const context = useContext(SettingsContext);

  if (context === null) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }

  return context;
}

type SettingsProviderProps = {
  value: Settings;
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
