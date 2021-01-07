import React, { FunctionComponent } from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import {
  ContentHeader,
  ContentHeaderButton,
  LoadingIndicator,
} from "../../Components";

import { Check, Group, Input, Message, Select, Text } from "../Components";

import { faSave } from "@fortawesome/free-solid-svg-icons";

interface Props {
  settings?: SystemSettings;
  languages: ExtendLanguage[];
  enabled: ExtendLanguage[];
}

function mapStateToProps({ system }: StoreState) {
  return {
    languages: system.languages.items,
    enabled: system.enabledLanguage,
    settings: system.settings.items,
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

  if (settings === undefined) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  const general = settings.general;
  const analytics = settings.analytics;

  return (
    <Container fluid>
      <Helmet>
        <title>General - Bazarr (Settings)</title>
      </Helmet>
      <Row>
        <ContentHeader>
          <ContentHeaderButton icon={faSave}>Save</ContentHeaderButton>
        </ContentHeader>
      </Row>
      <Row className="p-4">
        <Container>
          <Group header="Host">
            <Input name="Address">
              <Text placeholder="0.0.0.0" defaultValue={general.ip}></Text>
              <Message type="info">
                Valid IP4 address or '0.0.0.0' for all interfaces
              </Message>
            </Input>
            <Input name="Port">
              <Text placeholder="6767" defaultValue={general.port}></Text>
            </Input>
            <Input name="Base URL">
              <Text prefix="/"></Text>
              <Message type="info">Reverse proxy support</Message>
            </Input>
          </Group>
          <Group header="Security">
            <Input name="Authentication">
              <Select options={securityOptions} nullKey="none"></Select>
            </Input>
            <Input name="API Key">
              <Text disabled></Text>
            </Input>
          </Group>
          <Group header="Proxy">
            <Input>
              <Select options={proxyOptions} nullKey="none"></Select>
            </Input>
          </Group>
          <Group header="Logging">
            <Input>
              <Check label="Debug" defaultValue={general.debug}></Check>
              <Message type="info">
                Debug logging should only be enabled temporarily
              </Message>
            </Input>
          </Group>
          <Group header="Analytics">
            <Input>
              <Check label="Enabled" defaultValue={analytics.enabled}></Check>
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
      </Row>
    </Container>
  );
};

export default connect(mapStateToProps)(SettingsGeneralView);
