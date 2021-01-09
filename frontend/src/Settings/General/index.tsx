import React, { FunctionComponent, useState } from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import {
  ContentHeader,
  ContentHeaderButton,
  AsyncStateOverlay,
} from "../../Components";

import {
  Check,
  Group,
  Input,
  Message,
  Select,
  Text,
  CollapseBox,
} from "../Components";

import { faSave } from "@fortawesome/free-solid-svg-icons";

interface Props {
  settings: AsyncState<SystemSettings | undefined>;
  languages: ExtendLanguage[];
  enabled: ExtendLanguage[];
}

function mapStateToProps({ system }: StoreState) {
  return {
    languages: system.languages.items,
    enabled: system.enabledLanguage,
    settings: system.settings,
  };
}

const securityOptions = {
  none: "None",
  basic: "Basic",
  form: "Form",
};

const proxyOptions = {
  none: "None",
  socks: "Socks5",
  http: "HTTP(S)",
};

const SettingsGeneralView: FunctionComponent<Props> = (props) => {
  const { settings } = props;

  return (
    <AsyncStateOverlay state={settings}>
      {(item) => (
        <Container fluid>
          <Helmet>
            <title>General - Bazarr (Settings)</title>
          </Helmet>
          <Row>
            <ContentHeader>
              <ContentHeaderButton icon={faSave}>Save</ContentHeaderButton>
            </ContentHeader>
          </Row>
          <Row>
            <Container className="p-4">
              <Group header="Host">
                <Input name="Address">
                  <Text
                    placeholder="0.0.0.0"
                    defaultValue={item.general.ip}
                  ></Text>
                  <Message type="info">
                    Valid IPv4 address or '0.0.0.0' for all interfaces
                  </Message>
                </Input>
                <Input name="Port">
                  <Text
                    placeholder={6767}
                    defaultValue={item.general.port}
                  ></Text>
                </Input>
                <Input name="Base URL">
                  <Text prefix="/" defaultValue={item.general.base_url}></Text>
                  <Message type="info">Reverse proxy support</Message>
                </Input>
              </Group>
              <Group header="Security">
                <CollapseBox
                  indent
                  control={(change) => (
                    <Input name="Authentication">
                      <Select
                        options={securityOptions}
                        onChange={(val) => {
                          change(val !== "none");
                        }}
                        nullKey="none"
                      ></Select>
                    </Input>
                  )}
                >
                  <Input name="Username">
                    <Text></Text>
                  </Input>
                  <Input name="Password">
                    <Text></Text>
                  </Input>
                </CollapseBox>
                <Input name="API Key">
                  <Text disabled></Text>
                </Input>
              </Group>
              <Group header="Proxy">
                <CollapseBox
                  indent
                  control={(change) => (
                    <Input>
                      <Select
                        options={proxyOptions}
                        nullKey="none"
                        onChange={(val) => {
                          change(val !== "none");
                        }}
                      ></Select>
                    </Input>
                  )}
                >
                  <Input name="Host">
                    <Text></Text>
                  </Input>
                  <Input name="Port">
                    <Text></Text>
                  </Input>
                  <Input name="Username">
                    <Text></Text>
                  </Input>
                  <Input name="Password">
                    <Text></Text>
                    <Message type="info">
                      You only need to enter a username and password if one is
                      required. Leave them blank otherwise
                    </Message>
                  </Input>
                  <Input name="Ignored Addresses">
                    <Text defaultValue={item.proxy.exclude.join(",")}></Text>
                    <Message type="info">
                      Use ',' as a separator, and '*.' as a wildcard for
                      subdomains
                    </Message>
                  </Input>
                </CollapseBox>
              </Group>
              <Group header="Logging">
                <Input>
                  <Check
                    label="Debug"
                    defaultValue={item.general.debug}
                  ></Check>
                  <Message type="info">
                    Debug logging should only be enabled temporarily
                  </Message>
                </Input>
              </Group>
              <Group header="Analytics">
                <Input>
                  <Check
                    label="Enabled"
                    defaultValue={item.analytics.enabled}
                  ></Check>
                  <Message type="info">
                    Send anonymous usage information, nothing that can identify
                    you. This includes information on which providers you use,
                    what languages you search for, Bazarr, Python, Sonarr,
                    Radarr and what OS version you are using. We will use this
                    information to prioritize features and bug fixes. Please,
                    keep this enabled as this is the only way we have to better
                    understand how you use Bazarr.
                  </Message>
                </Input>
              </Group>
            </Container>
          </Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps)(SettingsGeneralView);
