import {
  createContext,
  FunctionComponent,
  PropsWithChildren,
  useContext,
} from "react";

const SettingsContext = createContext<Settings | null>(null);

export function useSettings() {
  const context = useContext(SettingsContext);

  return context;
}

type SettingsProviderProps = {
  value: Settings | null;
};

type Props = PropsWithChildren<SettingsProviderProps>;

export const SettingsProvider: FunctionComponent<Props> = ({
  value,
  children,
}) => {
  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};
