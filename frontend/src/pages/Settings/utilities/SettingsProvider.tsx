import { FunctionComponent, PropsWithChildren } from "react";
import { SettingsContext } from "@/pages/Settings/utilities/useSettings";

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
