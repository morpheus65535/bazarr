import { FunctionComponent, useState } from "react";
import { Group as MantineGroup } from "@mantine/core";
import { useClipboard } from "@mantine/hooks";
import {
  faCheck,
  faClipboard,
  faSync,
} from "@fortawesome/free-solid-svg-icons";
import { range } from "lodash";
import { useSystemStatus } from "@/apis/hooks";
import {
  Action,
  Check,
  Chips,
  CollapseBox,
  Layout,
  Message,
  Number,
  Password,
  Section,
  Selector,
  Text,
} from "@/pages/Settings/components";
import { toggleState } from "@/utilities";
import ExternalWebhookSelector from "./ExternalWebhookSelector";
import { proxyOptions, securityOptions } from "./options";

const characters = "abcdef0123456789";
const settingApiKey = "settings-auth-apikey";

const generateApiKey = () => {
  return Array(32)
    .fill(null)
    .map(() => characters.charAt(Math.floor(Math.random() * characters.length)))
    .join("");
};

const SettingsGeneralView: FunctionComponent = () => {
  const { data: status } = useSystemStatus();
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
        <Text
          label="Instance Name"
          settingKey="settings-general-instance_name"
        ></Text>
        <Message>Have a custom instance name as browser's tab title</Message>
        <Text label="Hostname" settingKey="settings-general-hostname"></Text>
        <Message>
          Hostname or IP address to access Bazarr (ie: bazarr.mydomain.local or
          192.168.0.100). Required for webhook security.
        </Message>
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
                    c={copied ? "success" : undefined}
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
                c="danger"
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
      <Section header="Jobs Manager">
        <Selector
          label="Concurrent Jobs"
          options={range(1, (status?.cpu_cores ?? 3) + 1).map((opt) => ({
            label: `${opt.toString()} ${opt === 1 ? "job" : "jobs"}`,
            value: opt,
          }))}
          settingKey="settings-general-concurrent_jobs"
        />
        <Message>
          Number of concurrent jobs allowed in the jobs manager.
          <br />
          This is useful to adjust the number of jobs that can be executed
          simultaneously. Exceeding jobs will be kept in pending queue until a
          slot becomes available.
          <br />
          Too much concurrent jobs can cause performance issues and affect
          system responsiveness. Setting too low can cause jobs to be queued for
          too long.
        </Message>
      </Section>
      <Section header="Incoming Webhooks">
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
    </Layout>
  );
};

export default SettingsGeneralView;
