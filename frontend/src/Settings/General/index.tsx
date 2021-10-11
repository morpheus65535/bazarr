import {
  faCheck,
  faClipboard,
  faSync,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useState } from "react";
import { InputGroup } from "react-bootstrap";
import { copyToClipboard, Environment, toggleState } from "../../utilities";
import {
  Button,
  Check,
  Chips,
  CollapseBox,
  Group,
  Input,
  Message,
  Selector,
  SettingsProvider,
  Text,
} from "../components";
import { branchOptions, proxyOptions, securityOptions } from "./options";

const characters = "abcdef0123456789";
const settingApiKey = "settings-auth-apikey";

const generateApiKey = () => {
  return Array(32)
    .fill(null)
    .map(() => characters.charAt(Math.floor(Math.random() * characters.length)))
    .join("");
};

const baseUrlOverride = (settings: Settings) =>
  settings.general.base_url?.slice(1) ?? "";

const SettingsGeneralView: FunctionComponent = () => {
  const [copied, setCopy] = useState(false);

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
                clearable
                options={securityOptions}
                settingKey="settings-auth-type"
                beforeStaged={(v) => (v === null ? "None" : v)}
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
            <Text disabled controlled settingKey={settingApiKey}></Text>
            <InputGroup.Append>
              <Button
                variant={copied ? "success" : "light"}
                settingKey={settingApiKey}
                onClick={(update, key, value) => {
                  if (value) {
                    copyToClipboard(value);
                    toggleState(setCopy, 1500);
                  }
                }}
              >
                <FontAwesomeIcon
                  icon={copied ? faCheck : faClipboard}
                ></FontAwesomeIcon>
              </Button>
              <Button
                variant="danger"
                settingKey={settingApiKey}
                onClick={(update, key) => {
                  update(generateApiKey(), key);
                }}
              >
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
                beforeStaged={(v) => (v === null ? "None" : v)}
              ></Selector>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content on={(k) => k !== "" && k !== "None"}>
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
              <Chips settingKey="settings-proxy-exclude"></Chips>
              <Message>
                List of excluded domains or IP addresses. Asterisk(wildcard),
                regex and CIDR are unsupported. You can use '.domain.com' to
                include all subdomains.
              </Message>
            </Input>
          </CollapseBox.Content>
        </CollapseBox>
      </Group>
      <Group header="Updates" hidden={!Environment.canUpdate}>
        <Input>
          <Check
            label="Automatic"
            settingKey="settings-general-auto_update"
          ></Check>
          <Message>Automatically download and install updates</Message>
        </Input>
        <Input>
          <Selector
            options={branchOptions}
            settingKey="settings-general-branch"
          ></Selector>
          <Message>Branch used by update mechanism</Message>
        </Input>
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
            you search for, Bazarr, Python and what OS version you are using. We
            will use this information to prioritize features and bug fixes.
            Please, keep this enabled as this is the only way we have to better
            understand how you use Bazarr.
          </Message>
        </Input>
      </Group>
    </SettingsProvider>
  );
};

export default SettingsGeneralView;
