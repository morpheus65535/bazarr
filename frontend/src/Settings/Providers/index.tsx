import React, { FunctionComponent } from "react";
import { Group, Input, SettingsProvider } from "../components";
import { ProviderView, ProviderModal } from "./components";

const SettingsProvidersView: FunctionComponent = () => {
  return (
    <SettingsProvider title="Providers - Bazarr (Settings)">
      <Group header="Providers">
        <Input>
          <ProviderView></ProviderView>
        </Input>
      </Group>
      <ProviderModal></ProviderModal>
    </SettingsProvider>
  );
};

export default SettingsProvidersView;
