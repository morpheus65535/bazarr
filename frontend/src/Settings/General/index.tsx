import React, { FunctionComponent } from "react";
import { Container, Button } from "react-bootstrap";
import { connect } from "react-redux";

import {
  Check,
  Group,
  Input,
  Selector,
  Message,
  Text,
  CollapseBox,
} from "../Components";

import SettingTemplate from "../Components/template";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSync, faClipboard } from "@fortawesome/free-solid-svg-icons";

interface Props {
  languages: ExtendLanguage[];
  enabled: ExtendLanguage[];
}

function mapStateToProps({ system }: StoreState) {
  return {
    languages: system.languages.items,
    enabled: system.enabledLanguage,
  };
}

const securityOptions = {
  none: "None",
  basic: "Basic",
  form: "Form",
};

const proxyOptions = {
  none: "None",
  socks5: "Socks5",
  http: "HTTP(S)",
};

const SettingsGeneralView: FunctionComponent<Props> = (props) => {
  return (
    <SettingTemplate title="General - Bazarr (Settings)">
      {(settings, update) => (
        <Container>
          <Group header="Host">
            <Input name="Address">
              <Text
                placeholder="0.0.0.0"
                defaultValue={settings.general.ip}
                onChange={(v) => update(v, "settings-general-ip")}
              ></Text>
              <Message type="info">
                Valid IPv4 address or '0.0.0.0' for all interfaces
              </Message>
            </Input>
            <Input name="Port">
              <Text
                placeholder={6767}
                defaultValue={settings.general.port}
                onChange={(v) => update(v, "settings-general-port")}
              ></Text>
            </Input>
            <Input name="Base URL">
              <Text
                prefix="/"
                defaultValue={settings.general.base_url}
                onChange={(v) => update(v, "settings-general-base_url")}
              ></Text>
              <Message type="info">Reverse proxy support</Message>
            </Input>
          </Group>
          <Group header="Security">
            <CollapseBox
              indent
              defaultOpen={settings.auth.type !== "none"}
              control={(change) => (
                <Input name="Authentication">
                  <Selector
                    options={securityOptions}
                    defaultKey={settings.auth.type}
                    onSelect={(v: string) => {
                      change(v !== "none");
                      update(v, "settings-auth-type");
                    }}
                    nullKey="none"
                  ></Selector>
                </Input>
              )}
            >
              <Input name="Username">
                <Text
                  defaultValue={settings.auth.username}
                  onChange={(v) => update(v, "settings-auth-username")}
                ></Text>
              </Input>
              <Input name="Password">
                <Text
                  password
                  defaultValue={settings.auth.password}
                  onChange={(v) => update(v, "settings-auth-password")}
                ></Text>
              </Input>
            </CollapseBox>
            <Input name="API Key">
              <Text
                disabled
                postfix={() => (
                  <React.Fragment>
                    <Button disabled variant="light">
                      <FontAwesomeIcon icon={faClipboard}></FontAwesomeIcon>
                    </Button>
                    <Button disabled variant="danger">
                      <FontAwesomeIcon icon={faSync}></FontAwesomeIcon>
                    </Button>
                  </React.Fragment>
                )}
                defaultValue={settings.auth.apikey}
                onChange={(v) => update(v, "settings-auth-apikey")}
              ></Text>
            </Input>
          </Group>
          <Group header="Proxy">
            <CollapseBox
              indent
              defaultOpen={settings.proxy.type !== "none"}
              control={(change) => (
                <Input>
                  <Selector
                    defaultKey={settings.proxy.type}
                    options={proxyOptions}
                    nullKey="none"
                    onSelect={(v: string) => {
                      change(v !== "none");
                      update(v, "settings-proxy-type");
                    }}
                  ></Selector>
                </Input>
              )}
            >
              <Input name="Host">
                <Text
                  defaultValue={settings.proxy.url}
                  onChange={(v) => update(v, "settings-proxy-url")}
                ></Text>
              </Input>
              <Input name="Port">
                <Text
                  defaultValue={settings.proxy.port}
                  onChange={(v) => update(v, "settings-proxy-port")}
                ></Text>
              </Input>
              <Input name="Username">
                <Text
                  defaultValue={settings.proxy.username}
                  onChange={(v) => update(v, "settings-proxy-username")}
                ></Text>
              </Input>
              <Input name="Password">
                <Text
                  password
                  defaultValue={settings.proxy.password}
                  onChange={(v) => update(v, "settings-proxy-password")}
                ></Text>
                <Message type="info">
                  You only need to enter a username and password if one is
                  required. Leave them blank otherwise
                </Message>
              </Input>
              <Input name="Ignored Addresses">
                <Text
                  defaultValue={settings.proxy.exclude.join(",")}
                  onChange={(v) => update(v, "settings-proxy-exclude")}
                ></Text>
                <Message type="info">
                  Use ',' as a separator, and '*.' as a wildcard for subdomains
                </Message>
              </Input>
            </CollapseBox>
          </Group>
          <Group header="Logging">
            <Input>
              <Check
                label="Debug"
                defaultValue={settings.general.debug}
                onChange={(v) => update(v, "settings-general-debug")}
              ></Check>
              <Message type="info">
                Debug logging should only be enabled temporarily
              </Message>
            </Input>
          </Group>
          <Group header="Analytics">
            <Input>
              <Check
                label="Enable"
                defaultValue={settings.analytics.enabled}
                onChange={(v) => update(v, "settings-analytics-enabled")}
              ></Check>
              <Message type="info">
                Send anonymous usage information, nothing that can identify you.
                This includes information on which providers you use, what
                languages you search for, Bazarr, Python, Sonarr, Radarr and
                what OS version you are using. We will use this information to
                prioritize features and bug fixes. Please, keep this enabled as
                this is the only way we have to better understand how you use
                Bazarr.
              </Message>
            </Input>
          </Group>
        </Container>
      )}
    </SettingTemplate>
  );
};

export default connect(mapStateToProps)(SettingsGeneralView);
