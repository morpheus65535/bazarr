import React, { FunctionComponent } from "react";

import {
  Group,
  Input,
  Text,
  Message,
  Check,
  SettingsProvider,
} from "../components";

import {
  ProviderSelector,
  UsernamePasswordInput,
  ProviderSection,
} from "./components";

const SettingsProvidersView: FunctionComponent = () => {
  return (
    <SettingsProvider title="Providers - Bazarr (Settings)">
      <Group header="Providers">
        <Input>
          <ProviderSelector></ProviderSelector>
        </Input>
      </Group>
      <ProviderSection providerKey="addic7ed">
        <UsernamePasswordInput settingKey="addic7ed"></UsernamePasswordInput>
      </ProviderSection>
      <ProviderSection providerKey="assrt">
        <Input name="Token">
          <Text settingKey="settings-assrt-token"></Text>
        </Input>
      </ProviderSection>
      <ProviderSection providerKey="betaseries">
        <Input name="API Key">
          <Text settingKey="settings-betaseries-token"></Text>
        </Input>
      </ProviderSection>
      <ProviderSection providerKey="legendasdivx">
        <UsernamePasswordInput settingKey="legendasdivx"></UsernamePasswordInput>
      </ProviderSection>
      <ProviderSection providerKey="legendastv">
        <UsernamePasswordInput settingKey="legendastv"></UsernamePasswordInput>
      </ProviderSection>
      <ProviderSection providerKey="napisy24">
        <UsernamePasswordInput settingKey="napisy24"></UsernamePasswordInput>
        <Message type="info">
          The provided credentials must have API access. Leave empty to use the
          defaults.
        </Message>
      </ProviderSection>
      <ProviderSection providerKey="opensubtitles">
        <UsernamePasswordInput settingKey="opensubtitles"></UsernamePasswordInput>
        <Input>
          <Check
            settingKey="settings-opensubtitles-vip"
            inline
            label="VIP"
          ></Check>
          <Check
            settingKey="settings-opensubtitles-ssl"
            inline
            label="Use SSL"
          ></Check>
          <Check
            settingKey="settings-opensubtitles-skip_wrong_fps"
            inline
            label="Skip Wrong FPS"
          ></Check>
        </Input>
      </ProviderSection>
      <ProviderSection providerKey="subscene">
        <UsernamePasswordInput settingKey="subscene"></UsernamePasswordInput>
      </ProviderSection>
      <ProviderSection providerKey="titlovi">
        <UsernamePasswordInput settingKey="titlovi"></UsernamePasswordInput>
      </ProviderSection>
      <ProviderSection providerKey="xsubs">
        <UsernamePasswordInput settingKey="xsubs"></UsernamePasswordInput>
      </ProviderSection>
    </SettingsProvider>
  );
};

export default SettingsProvidersView;
