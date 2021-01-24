import React, { FunctionComponent, useContext, useMemo } from "react";
import { Container } from "react-bootstrap";

import { capitalize } from "lodash";

import { Group, Input, Text, Check, Message, Selector } from "../components";
import SettingTemplate, { UpdateContext } from "../components/template";

import { ProviderList } from "./list";

const SettingsContext = React.createContext<SystemSettings | undefined>(
  undefined
);

const EnabledContext = React.createContext<string[]>([]);

interface ProviderEditProps {
  providerKey: string;
}

const ProviderEditSection: FunctionComponent<ProviderEditProps> = ({
  providerKey,
  children,
}) => {
  const enabled = useContext(EnabledContext);

  const info = useMemo(() => ProviderList.find((v) => v.key === providerKey), [
    providerKey,
  ]);

  const show = useMemo(
    () => enabled.findIndex((v) => v === providerKey) !== -1,
    [enabled, providerKey]
  );

  const header = useMemo(() => {
    const name = info?.name;

    if (name) {
      return name;
    } else {
      return capitalize(providerKey);
    }
  }, [providerKey, info]);

  return (
    <Group hidden={!show} header={header}>
      {children}
      {info && info.description && (
        <Message type="info">{info?.description}</Message>
      )}
    </Group>
  );
};

interface SelectorProps {}

const ProviderSelector: FunctionComponent<SelectorProps> = () => {
  const enabled = useContext(EnabledContext);

  const update = useContext(UpdateContext);

  const providers = useMemo<Pair[]>(
    () =>
      ProviderList.map((v) => ({
        key: v.key,
        value: v.name ? v.name : capitalize(v.key),
      })),
    []
  );
  return (
    <Selector
      multiple
      options={providers}
      defaultKey={enabled}
      onMultiSelect={(keys) => {
        update(keys, "settings-general-enabled_providers");
      }}
    ></Selector>
  );
};

const UsernamePasswordInput: FunctionComponent<{
  settingKey: keyof SystemSettings;
}> = ({ settingKey }) => {
  const update = useContext(UpdateContext);

  return (
    <React.Fragment>
      <Input name="Username">
        <Text
          onChange={(v) => update(v, `settings-${settingKey}-username`)}
        ></Text>
      </Input>
      <Input name="Password">
        <Text
          password
          onChange={(v) => update(v, `settings-${settingKey}-password`)}
        ></Text>
      </Input>
    </React.Fragment>
  );
};

function getEnabledList(settings: GeneralSettings, changed: LooseObject) {
  if ("settings-general-enabled_providers" in changed) {
    return changed["settings-general-enabled_providers"];
  } else {
    return settings.enabled_providers;
  }
}

const SettingsProvidersView: FunctionComponent = () => {
  return (
    <SettingTemplate title="Providers - Bazarr (Settings)">
      {(settings, update, changed) => (
        <SettingsContext.Provider value={settings}>
          <EnabledContext.Provider
            value={getEnabledList(settings.general, changed)}
          >
            <Container>
              <Group header="Providers">
                <Input>
                  <ProviderSelector></ProviderSelector>
                </Input>
              </Group>
              <ProviderEditSection providerKey="addic7ed">
                <UsernamePasswordInput settingKey="addic7ed"></UsernamePasswordInput>
              </ProviderEditSection>
              <ProviderEditSection providerKey="assrt">
                <Input name="Token">
                  <Text></Text>
                </Input>
              </ProviderEditSection>
              <ProviderEditSection providerKey="betaseries">
                <Input name="API Key">
                  <Text></Text>
                </Input>
              </ProviderEditSection>
              <ProviderEditSection providerKey="legendasdivx">
                <UsernamePasswordInput settingKey="legendasdivx"></UsernamePasswordInput>
              </ProviderEditSection>
              <ProviderEditSection providerKey="legendastv">
                <UsernamePasswordInput settingKey="legendastv"></UsernamePasswordInput>
              </ProviderEditSection>
              <ProviderEditSection providerKey="napisy24">
                <UsernamePasswordInput settingKey="napisy24"></UsernamePasswordInput>
                <Message type="info">
                  The provided credentials must have API access. Leave empty to
                  use the defaults.
                </Message>
              </ProviderEditSection>
              <ProviderEditSection providerKey="opensubtitles">
                <UsernamePasswordInput settingKey="opensubtitles"></UsernamePasswordInput>
                <Input>
                  <Check inline label="VIP"></Check>
                  <Check inline label="Use SSL"></Check>
                  <Check inline label="Skip Wrong FPS"></Check>
                </Input>
              </ProviderEditSection>
              <ProviderEditSection providerKey="subscene">
                <UsernamePasswordInput settingKey="subscene"></UsernamePasswordInput>
              </ProviderEditSection>
              <ProviderEditSection providerKey="titlovi">
                <UsernamePasswordInput settingKey="titlovi"></UsernamePasswordInput>
              </ProviderEditSection>
              <ProviderEditSection providerKey="xsubs">
                <UsernamePasswordInput settingKey="xsubs"></UsernamePasswordInput>
              </ProviderEditSection>
            </Container>
          </EnabledContext.Provider>
        </SettingsContext.Provider>
      )}
    </SettingTemplate>
  );
};

export default SettingsProvidersView;
