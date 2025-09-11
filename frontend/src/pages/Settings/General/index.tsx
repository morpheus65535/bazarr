import { FunctionComponent, useState } from "react";
import { Box, Group as MantineGroup, Text as MantineText } from "@mantine/core";
import { useClipboard } from "@mantine/hooks";
import {
  faCheck,
  faClipboard,
  faSync,
} from "@fortawesome/free-solid-svg-icons";
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
} from "@/pages/Settings/components";
import { Environment, toggleState } from "@/utilities";
import ExternalWebhookSelector from "./ExternalWebhookSelector";
import { branchOptions, proxyOptions, securityOptions } from "./options";

const characters = "abcdef0123456789";
const settingApiKey = "settings-auth-apikey";

const generateApiKey = () => {
  return Array(32)
    .fill(null)
    .map(() => characters.charAt(Math.floor(Math.random() * characters.length)))
    .join("");
};

const SettingsGeneralView: FunctionComponent = () => {
  const [copied, setCopy] = useState(false);

  const clipboard = useClipboard();

  return (
    <Layout name="General">
      <Section header="Host">
        <Text
          label="Address"
          placeholder="*"
          settingKey="settings-general-ip"
        ></Text>
        <Message>Valid IP address or '*' for all interfaces</Message>
        <Number
          label="Port"
          placeholder="6767"
          settingKey="settings-general-port"
        ></Number>
        <Text
          label="Base URL"
          leftSection="/"
          settingKey="settings-general-base_url"
          settingOptions={{
            onLoaded: (s) => s.general.base_url?.slice(1) ?? "",
            onSubmit: (v) => "/" + v,
          }}
        ></Text>
        <Message>Reverse proxy support</Message>
      </Section>
      <Section header="Security">
        <Selector
          label="Authentication"
          clearable
          options={securityOptions}
          placeholder="No Authentication"
          settingKey="settings-auth-type"
        ></Selector>
        <CollapseBox settingKey="settings-auth-type">
          <Text label="Username" settingKey="settings-auth-username"></Text>
          <Password
            label="Password"
            settingKey="settings-auth-password"
          ></Password>
        </CollapseBox>
        <Text
          label="API Key"
          // User can copy through the clipboard button
          disabled={window.isSecureContext}
          // Enable user to at least copy when not in secure context
          readOnly={!window.isSecureContext}
          rightSectionWidth={95}
          rightSectionProps={{ style: { justifyContent: "flex-end" } }}
          rightSection={
            <MantineGroup gap="xs" mx="xs" justify="right">
              {
                // Clipboard API is only available in secure contexts See: https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API#interfaces
                window.isSecureContext && (
                  <Action
                    label="Copy API Key"
                    settingKey={settingApiKey}
                    c={copied ? "green" : undefined}
                    icon={copied ? faCheck : faClipboard}
                    onClick={(update, value) => {
                      if (value) {
                        clipboard.copy(value);
                        toggleState(setCopy, 1500);
                      }
                    }}
                  />
                )
              }
              <Action
                label="Regenerate"
                settingKey={settingApiKey}
                c="red"
                icon={faSync}
                onClick={(update) => {
                  update(generateApiKey());
                }}
              ></Action>
            </MantineGroup>
          }
          settingKey={settingApiKey}
        ></Text>
        <Check
          label="Enable CORS headers"
          settingKey="settings-cors-enabled"
        ></Check>
        <Message>
          Allow third parties to make requests towards your Bazarr installation.
          Requires a restart of Bazarr when changed
        </Message>
      </Section>
      <Section header="External Integrations">
        <ExternalWebhookSelector />
      </Section>
      <Section header="Proxy">
        <Selector
          clearable
          settingKey="settings-proxy-type"
          placeholder="No Proxy"
          options={proxyOptions}
        ></Selector>
        <CollapseBox
          settingKey="settings-proxy-type"
          on={(k) => k !== null && k !== "None"}
        >
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
            List of excluded domains or IP addresses. Asterisk(wildcard), regex
            and CIDR are unsupported. You can use '.domain.com' to include all
            subdomains.
          </Message>
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
        <Text
          label="Include Filter"
          settingKey="settings-log-include_filter"
        ></Text>
        <Text
          label="Exclude Filter"
          settingKey="settings-log-exclude_filter"
        ></Text>
        <Check
          label="Use Regular Expressions (Regex)"
          settingKey="settings-log-use_regex"
        ></Check>
        <Check
          label="Ignore Case"
          settingKey="settings-log-ignore_case"
        ></Check>
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
          rightSection={
            <Box w="4rem" style={{ justifyContent: "flex-end" }}>
              <MantineText size="xs" px="sm" c="dimmed">
                Days
              </MantineText>
            </Box>
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
