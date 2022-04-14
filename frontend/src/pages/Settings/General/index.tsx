import { Environment, toggleState } from "@/utilities";
import {
  faCheck,
  faClipboard,
  faSync,
} from "@fortawesome/free-solid-svg-icons";
import { Group as MantineGroup, Text as MantineText } from "@mantine/core";
import { useClipboard } from "@mantine/hooks";
import { FunctionComponent, useState } from "react";
import {
  Action,
  Check,
  Chips,
  CollapseBox,
  File,
  Layout,
  Message,
  Number,
  Password,
  Section,
  Selector,
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

  const clipboard = useClipboard();

  return (
    <Layout name="General">
      <Section header="Host">
        <Text
          label="Address"
          placeholder="0.0.0.0"
          settingKey="settings-general-ip"
        ></Text>
        <Message>Valid IPv4 address or '0.0.0.0' for all interfaces</Message>
        <Number
          label="Port"
          placeholder="6767"
          settingKey="settings-general-port"
        ></Number>
        <Text
          label="Base URL"
          icon="/"
          settingKey="settings-general-base_url"
          override={baseUrlOverride}
          beforeStaged={(v) => "/" + v}
        ></Text>
        <Message>Reverse proxy support</Message>
      </Section>
      <Section header="Security">
        <CollapseBox>
          <CollapseBox.Control>
            <Selector
              label="Authentication"
              clearable
              options={securityOptions}
              settingKey="settings-auth-type"
              beforeStaged={(v) => (v === null ? "None" : v)}
            ></Selector>
          </CollapseBox.Control>
          <CollapseBox.Content on={(k) => k !== "" && k !== "None"}>
            <Text label="Username" settingKey="settings-auth-username"></Text>
            <Password
              label="Password"
              settingKey="settings-auth-password"
            ></Password>
          </CollapseBox.Content>
        </CollapseBox>
        <Text
          label="API Key"
          disabled
          rightSectionWidth={95}
          rightSectionProps={{ style: { justifyContent: "flex-end" } }}
          rightSection={
            <MantineGroup spacing="xs" mx="xs" position="right">
              <Action
                variant="light"
                settingKey={settingApiKey}
                color={copied ? "green" : undefined}
                icon={copied ? faCheck : faClipboard}
                onClick={(update, key, value) => {
                  if (value) {
                    clipboard.copy(value);
                    toggleState(setCopy, 1500);
                  }
                }}
              ></Action>
              <Action
                variant="light"
                settingKey={settingApiKey}
                color="red"
                icon={faSync}
                onClick={(update, key) => {
                  update(generateApiKey(), key);
                }}
              ></Action>
            </MantineGroup>
          }
          settingKey={settingApiKey}
        ></Text>
      </Section>
      <Section header="Proxy">
        <CollapseBox>
          <CollapseBox.Control>
            <Selector
              clearable
              settingKey="settings-proxy-type"
              options={proxyOptions}
              beforeStaged={(v) => (v === null ? "None" : v)}
            ></Selector>
          </CollapseBox.Control>
          <CollapseBox.Content on={(k) => k !== "" && k !== "None"}>
            <Text label="Host" settingKey="settings-proxy-url"></Text>
            <Number label="Port" settingKey="settings-proxy-port"></Number>
            <Text label="Username" settingKey="settings-proxy-username"></Text>
            <Password
              label="Password"
              settingKey="settings-proxy-password"
            ></Password>
            <Message>
              You only need to enter a username and password if one is required.
              Leave them blank otherwise
            </Message>
            <Chips
              label="Ignored Addresses"
              settingKey="settings-proxy-exclude"
            ></Chips>
            <Message>
              List of excluded domains or IP addresses. Asterisk(wildcard),
              regex and CIDR are unsupported. You can use '.domain.com' to
              include all subdomains.
            </Message>
          </CollapseBox.Content>
        </CollapseBox>
      </Section>
      <Section header="Updates" hidden={!Environment.canUpdate}>
        <Check
          label="Automatic"
          settingKey="settings-general-auto_update"
        ></Check>
        <Message>Automatically download and install updates</Message>
        <Selector
          options={branchOptions}
          settingKey="settings-general-branch"
        ></Selector>
        <Message>Branch used by update mechanism</Message>
      </Section>
      <Section header="Logging">
        <Check label="Debug" settingKey="settings-general-debug"></Check>
        <Message>Debug logging should only be enabled temporarily</Message>
      </Section>
      <Section header="Backups">
        <File
          label="Folder"
          settingKey="settings-backup-folder"
          type="bazarr"
        ></File>
        <Message>Absolute path to the backup directory</Message>
        <Number
          label="Retention"
          settingKey="settings-backup-retention"
          styles={{
            rightSection: { width: "4rem", justifyContent: "flex-end" },
          }}
          rightSection={
            <MantineText size="xs" px="sm" color="dimmed">
              Days
            </MantineText>
          }
        ></Number>
      </Section>
      <Section header="Analytics">
        <Check label="Enable" settingKey="settings-analytics-enabled"></Check>
        <Message>
          Send anonymous usage information, nothing that can identify you. This
          includes information on which providers you use, what languages you
          search for, Bazarr, Python, Sonarr, Radarr and what OS version you are
          using. We will use this information to prioritize features and bug
          fixes. Please, keep this enabled as this is the only way we have to
          better understand how you use Bazarr.
        </Message>
      </Section>
    </Layout>
  );
};

export default SettingsGeneralView;
