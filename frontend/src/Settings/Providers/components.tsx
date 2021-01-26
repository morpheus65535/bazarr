import React, { FunctionComponent, useMemo } from "react";
import { ProviderList } from "./list";
import {
  Selector,
  Input,
  Text,
  Group,
  Message,
  useLatest,
} from "../components";

import { capitalize, isArray } from "lodash";

export const ProviderSelector: FunctionComponent = () => {
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
      settingKey="settings-general-enabled_providers"
      options={providers}
    ></Selector>
  );
};

export const UsernamePasswordInput: FunctionComponent<{
  settingKey: keyof SystemSettings;
}> = ({ settingKey }) => {
  return (
    <React.Fragment>
      <Input name="Username">
        <Text settingKey={`settings-${settingKey}-username`}></Text>
      </Input>
      <Input name="Password">
        <Text password settingKey={`settings-${settingKey}-password`}></Text>
      </Input>
    </React.Fragment>
  );
};

interface ProviderEditProps {
  providerKey: string;
}

export const ProviderSection: FunctionComponent<ProviderEditProps> = ({
  providerKey,
  children,
}) => {
  const info = useMemo(() => ProviderList.find((v) => v.key === providerKey), [
    providerKey,
  ]);

  const enabled = useLatest<string[]>(
    "settings-general-enabled_providers",
    isArray
  );

  const hide = useMemo(() => {
    if (enabled) {
      return enabled.findIndex((v) => v === providerKey) === -1;
    } else {
      return true;
    }
  }, [enabled, providerKey]);

  const header = useMemo(() => {
    const name = info?.name;

    if (name) {
      return name;
    } else {
      return capitalize(providerKey);
    }
  }, [providerKey, info]);

  return (
    <Group hidden={hide} header={header}>
      {children}
      {info && info.description && (
        <Message type="info">{info?.description}</Message>
      )}
    </Group>
  );
};
