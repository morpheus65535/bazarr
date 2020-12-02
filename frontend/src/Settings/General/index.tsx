import React from "react";
import { Container, Form, InputGroup, Button } from "react-bootstrap";
import { connect } from "react-redux";

import { SettingGroup } from "../../components";
import ContentHeader, {
  ContentHeaderButton,
} from "../../components/ContentHeader";
import { CommonFormGroup } from "../../components/CommonForm";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSave, faSync } from "@fortawesome/free-solid-svg-icons";

interface Props {}

interface State {
  proxySelection: string;
  authSelection: string;
}

// function mapStateToProps({ system }: StoreState) {
//   return {
//     languages: system.languages.items,
//     enabled: system.enabledLanguage,
//   };
// }

const SelectionDefault = "None";
const AuthOptions = [
  ["None", SelectionDefault],
  ["Basic", "Basic"],
  ["Form", "Form"],
];

const ProxyOptions = [
  ["None", SelectionDefault],
  ["http", "HTTP(S)"],
  ["socks4", "Socks4"],
  ["socks5", "Socks5"],
];

const PageSizeOptions = ["Unlimited", 25, 50, 100, 250, 500, 1000];
const PageSizeManualSearchOptions = [5, 10, 15, 20, 25];

const formControlClass = "w-50";

class SettingsGeneralView extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      proxySelection: SelectionDefault,
      authSelection: SelectionDefault,
    };
  }

  onProxyChanged(value: string) {
    this.setState({
      ...this.state,
      proxySelection: value,
    });
  }

  onAuthChanged(value: string) {
    this.setState({
      ...this.state,
      authSelection: value,
    });
  }

  render(): JSX.Element {
    const { proxySelection, authSelection } = this.state;

    const host: JSX.Element = (
      <SettingGroup name="Host">
        <CommonFormGroup title="Bind Address">
          <Form.Control type="text" className={formControlClass}></Form.Control>
          <Form.Label>
            Valid IP4 address or '0.0.0.0' for all interfaces
          </Form.Label>
          <Form.Label className="text-warning">
            Requires restart to take effect
          </Form.Label>
        </CommonFormGroup>
        <CommonFormGroup title="Port Number">
          <Form.Control type="text" className={formControlClass}></Form.Control>
          <Form.Label className="text-warning">
            Requires restart to take effect
          </Form.Label>
        </CommonFormGroup>
        <CommonFormGroup title="URL Base">
          <Form.Control type="text" className={formControlClass}></Form.Control>
          <Form.Label>For reverse proxy support, default is '/'</Form.Label>
          <Form.Label className="text-warning">
            Requires restart to take effect
          </Form.Label>
        </CommonFormGroup>
      </SettingGroup>
    );

    const security: JSX.Element = (
      <SettingGroup name="Security">
        <CommonFormGroup title="Authentication">
          <Form.Control
            as="select"
            className={formControlClass}
            onChange={(event) => {
              this.onAuthChanged(event.target.value);
            }}
          >
            {AuthOptions.map((val, idx) => (
              <option key={idx} value={val[0]}>
                {val[1]}
              </option>
            ))}
          </Form.Control>
          <Form.Label>
            Require Username and Password to access Bazarr
          </Form.Label>
        </CommonFormGroup>
        <div hidden={authSelection === SelectionDefault}>
          <CommonFormGroup title="Username">
            <Form.Control
              type="text"
              className={formControlClass}
            ></Form.Control>
          </CommonFormGroup>
          <CommonFormGroup title="Password">
            <Form.Control
              type="text"
              className={formControlClass}
            ></Form.Control>
          </CommonFormGroup>
        </div>
        <CommonFormGroup title="API Key">
          <InputGroup className={formControlClass}>
            <Form.Control type="text" disabled></Form.Control>
            <InputGroup.Append>
              <Button variant="danger">
                <FontAwesomeIcon icon={faSync}></FontAwesomeIcon>
              </Button>
            </InputGroup.Append>
          </InputGroup>
        </CommonFormGroup>
      </SettingGroup>
    );

    const proxy: JSX.Element = (
      <SettingGroup name="Proxy">
        <CommonFormGroup title="Type">
          <Form.Control
            as="select"
            className={formControlClass}
            onChange={(event) => {
              this.onProxyChanged(event.target.value);
            }}
          >
            {ProxyOptions.map((val, idx) => (
              <option key={idx} value={val[0]}>
                {val[1]}
              </option>
            ))}
          </Form.Control>
        </CommonFormGroup>
        <div hidden={proxySelection === SelectionDefault}>
          <CommonFormGroup title="Hostname">
            <Form.Control
              type="text"
              className={formControlClass}
            ></Form.Control>
          </CommonFormGroup>
          <CommonFormGroup title="Port">
            <Form.Control
              type="text"
              className={formControlClass}
            ></Form.Control>
          </CommonFormGroup>
          <CommonFormGroup title="Username">
            <Form.Control
              type="text"
              className={formControlClass}
            ></Form.Control>
          </CommonFormGroup>
          <CommonFormGroup title="Password">
            <Form.Control
              type="text"
              className={formControlClass}
            ></Form.Control>
            <Form.Label>
              You only need to enter a username and password if one is required.
              Leave them blank otherwise.
            </Form.Label>
          </CommonFormGroup>
          <CommonFormGroup title="Ignored Addresses">
            <Form.Control
              type="text"
              className={formControlClass}
            ></Form.Control>
          </CommonFormGroup>
        </div>
      </SettingGroup>
    );

    const ui: JSX.Element = (
      <SettingGroup name="UI">
        <CommonFormGroup title="Page Size">
          <Form.Control as="select" className={formControlClass}>
            {PageSizeOptions.map((val, idx) => (
              <option key={idx}>{val}</option>
            ))}
          </Form.Control>
        </CommonFormGroup>
        <CommonFormGroup title="Page Size Manual Search">
          <Form.Control as="select" className={formControlClass}>
            {PageSizeManualSearchOptions.map((val, idx) => (
              <option key={idx}>{val}</option>
            ))}
          </Form.Control>
        </CommonFormGroup>
      </SettingGroup>
    );

    const logging: JSX.Element = (
      <SettingGroup name="Logging">
        <CommonFormGroup title="Debug">
          <Form.Check type="checkbox"></Form.Check>
          <Form.Label>
            Debug logging should only be enabled temporarily
          </Form.Label>
        </CommonFormGroup>
      </SettingGroup>
    );

    const analytics: JSX.Element = (
      <SettingGroup name="Analytics">
        <CommonFormGroup title="Enabled">
          <Form.Check type="checkbox"></Form.Check>
          <Form.Label>
            Send anonymous usage information, nothing that can identify you.
            This includes information on which providers you use, what languages
            you search for, Bazarr, Python, Sonarr, Radarr and what OS version
            you are using. We will use this information to prioritize features
            and bug fixes. Please, keep this enabled as this is the only way we
            have to better understand how you use Bazarr.
          </Form.Label>
        </CommonFormGroup>
      </SettingGroup>
    );

    return (
      <Container fluid className="p-0">
        <ContentHeader>
          <ContentHeaderButton iconProps={{ icon: faSave }}>
            Save
          </ContentHeaderButton>
        </ContentHeader>
        <Form className="p-4">
          {host}
          {security}
          {proxy}
          {ui}
          {logging}
          {analytics}
        </Form>
      </Container>
    );
  }
}

export default connect()(SettingsGeneralView);
