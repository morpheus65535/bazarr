import React, { FunctionComponent, useCallback } from "react";
import { Button, InputGroup } from "react-bootstrap";

import {
  Check,
  Group,
  Input,
  Selector,
  Message,
  Text,
  CollapseBox,
  SettingsProvider,
} from "../components";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSync, faClipboard } from "@fortawesome/free-solid-svg-icons";

import { proxyOptions, securityOptions } from "./options";

const SettingsGeneralView: FunctionComponent = () => {
  const baseUrlOverride = useCallback((settings: SystemSettings) => {
    return settings.general.base_url?.slice(1) ?? "";
  }, []);

  return (
    <SettingsProvider title="General - Bazarr (Settings)">
      <Group header="Host">
        <Input name="Address">
          <Text placeholder="0.0.0.0" settingKey="settings-general-ip"></Text>
          <Message>Valid IPv4 address or '0.0.0.0' for all interfaces</Message>
        </Input>
        <Input name="Port">
          <Text placeholder={6767} settingKey="settings-general-port"></Text>
        </Input>
        <Input name="Base URL">
          <InputGroup>
            <InputGroup.Prepend>
              <InputGroup.Text>/</InputGroup.Text>
            </InputGroup.Prepend>
            <Text
              settingKey="settings-general-base_url"
              override={baseUrlOverride}
              beforeStaged={(v) => "/" + v}
            ></Text>
          </InputGroup>
          <Message>Reverse proxy support</Message>
        </Input>
      </Group>
      <Group header="Security">
        <CollapseBox>
          <CollapseBox.Control>
            <Input name="Authentication">
              <Selector
                // No Support yet
                disabled
                clearable
                options={securityOptions}
                settingKey="settings-auth-type"
                beforeStaged={(v) => (v === undefined ? "None" : v)}
              ></Selector>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content on={(k) => k !== "" && k !== "None"}>
            <Input name="Username">
              <Text settingKey="settings-auth-username"></Text>
            </Input>
            <Input name="Password">
              <Text password settingKey="settings-auth-password"></Text>
            </Input>
          </CollapseBox.Content>
        </CollapseBox>
        <Input name="API Key">
          <InputGroup>
            <Text disabled settingKey="settings-auth-apikey"></Text>
            <InputGroup.Append>
              <Button disabled variant="light">
                <FontAwesomeIcon icon={faClipboard}></FontAwesomeIcon>
              </Button>
              <Button disabled variant="danger">
                <FontAwesomeIcon icon={faSync}></FontAwesomeIcon>
              </Button>
            </InputGroup.Append>
          </InputGroup>
        </Input>
      </Group>
      <Group header="Proxy">
        <CollapseBox>
          <CollapseBox.Control>
            <Input>
              <Selector
                clearable
                settingKey="settings-proxy-type"
                options={proxyOptions}
                beforeStaged={(v) => (v === undefined ? "None" : v)}
              ></Selector>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content on={(k) => k !== "" && k !== "none"}>
            <Input name="Host">
              <Text settingKey="settings-proxy-url"></Text>
            </Input>
            <Input name="Port">
              <Text settingKey="settings-proxy-port"></Text>
            </Input>
            <Input name="Username">
              <Text settingKey="settings-proxy-username"></Text>
            </Input>
            <Input name="Password">
              <Text password settingKey="settings-proxy-password"></Text>
              <Message>
                You only need to enter a username and password if one is
                required. Leave them blank otherwise
              </Message>
            </Input>
            <Input name="Ignored Addresses">
              <Text
                settingKey="settings-proxy-exclude"
                override={(settings) => settings.proxy.exclude.join(",")}
              ></Text>
              <Message>
                Use ',' as a separator, and '*.' as a wildcard for subdomains
              </Message>
            </Input>
          </CollapseBox.Content>
        </CollapseBox>
      </Group>
      <Group header="Logging">
        <Input>
          <Check label="Debug" settingKey="settings-general-debug"></Check>
          <Message>Debug logging should only be enabled temporarily</Message>
        </Input>
      </Group>
      <Group header="Analytics">
        <Input>
          <Check label="Enable" settingKey="settings-analytics-enabled"></Check>
          <Message>
            Send anonymous usage information, nothing that can identify you.
            This includes information on which providers you use, what languages
            you search for, Bazarr, Python, Sonarr, Radarr and what OS version
            you are using. We will use this information to prioritize features
            and bug fixes. Please, keep this enabled as this is the only way we
            have to better understand how you use Bazarr.
          </Message>
        </Input>
      </Group>
    </SettingsProvider>
  );
};

export default SettingsGeneralView;
