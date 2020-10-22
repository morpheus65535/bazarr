import React from "react";
import { Container, Form, InputGroup, Button } from "react-bootstrap";
import { connect } from "react-redux";

import TitleBlock from "../../components/TitleBlock";
import { CommonHeader, CommonHeaderBtn } from "../../components/CommonHeader";
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

class SettingsGeneral extends React.Component<Props, State> {
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
      <TitleBlock title="Host">
        <CommonFormGroup title="Bind Address">
          <Form.Control type="text" className="w-50"></Form.Control>
          <Form.Label>
            Valid IP4 address or '0.0.0.0' for all interfaces
          </Form.Label>
          <Form.Label className="text-warning">
            Requires restart to take effect
          </Form.Label>
        </CommonFormGroup>
        <CommonFormGroup title="Port Number">
          <Form.Control type="text" className="w-50"></Form.Control>
          <Form.Label className="text-warning">
            Requires restart to take effect
          </Form.Label>
        </CommonFormGroup>
        <CommonFormGroup title="URL Base">
          <Form.Control type="text" className="w-50"></Form.Control>
          <Form.Label>For reverse proxy support, default is '/'</Form.Label>
          <Form.Label className="text-warning">
            Requires restart to take effect
          </Form.Label>
        </CommonFormGroup>
      </TitleBlock>
    );

    const security: JSX.Element = (
      <TitleBlock title="Security">
        <CommonFormGroup title="Authentication">
          <Form.Control
            as="select"
            className="w-50"
            onChange={(event) => {
              this.onAuthChanged(event.target.value);
            }}
          >
            {AuthOptions.map((val) => (
              <option value={val[0]}>{val[1]}</option>
            ))}
          </Form.Control>
          <Form.Label>
            Require Username and Password to access Bazarr
          </Form.Label>
        </CommonFormGroup>
        <div hidden={authSelection === SelectionDefault}>
          <CommonFormGroup title="Username">
            <Form.Control type="text" className="w-50"></Form.Control>
          </CommonFormGroup>
          <CommonFormGroup title="Password">
            <Form.Control type="text" className="w-50"></Form.Control>
          </CommonFormGroup>
        </div>
        <CommonFormGroup title="API Key">
          <InputGroup className="w-50">
            <Form.Control type="text" disabled></Form.Control>
            <InputGroup.Append>
              <Button variant="danger">
                <FontAwesomeIcon icon={faSync}></FontAwesomeIcon>
              </Button>
            </InputGroup.Append>
          </InputGroup>
        </CommonFormGroup>
      </TitleBlock>
    );

    const proxy: JSX.Element = (
      <TitleBlock title="Proxy">
        <CommonFormGroup title="Type">
          <Form.Control
            as="select"
            className="w-50"
            onChange={(event) => {
              this.onProxyChanged(event.target.value);
            }}
          >
            {ProxyOptions.map((val) => (
              <option value={val[0]}>{val[1]}</option>
            ))}
          </Form.Control>
        </CommonFormGroup>
        <div hidden={proxySelection === SelectionDefault}>
          <CommonFormGroup title="Hostname">
            <Form.Control type="text" className="w-50"></Form.Control>
          </CommonFormGroup>
          <CommonFormGroup title="Port">
            <Form.Control type="text" className="w-50"></Form.Control>
          </CommonFormGroup>
          <CommonFormGroup title="Username">
            <Form.Control type="text" className="w-50"></Form.Control>
          </CommonFormGroup>
          <CommonFormGroup title="Password">
            <Form.Control type="text" className="w-50"></Form.Control>
            <Form.Label>
              You only need to enter a username and password if one is required.
              Leave them blank otherwise.
            </Form.Label>
          </CommonFormGroup>
          <CommonFormGroup title="Ignored Addresses">
            <Form.Control type="text" className="w-50"></Form.Control>
          </CommonFormGroup>
        </div>
      </TitleBlock>
    );

    const ui: JSX.Element = (
      <TitleBlock title="UI">
        <CommonFormGroup title="Page Size">
          <Form.Control as="select" className="w-50">
            {PageSizeOptions.map((val) => (
              <option>{val}</option>
            ))}
          </Form.Control>
        </CommonFormGroup>
        <CommonFormGroup title="Page Size Manual Search">
          <Form.Control as="select" className="w-50">
            {PageSizeManualSearchOptions.map((val) => (
              <option>{val}</option>
            ))}
          </Form.Control>
        </CommonFormGroup>
      </TitleBlock>
    );

    const logging: JSX.Element = (
      <TitleBlock title="Logging">
        <CommonFormGroup title="Debug">
          <Form.Check type="checkbox"></Form.Check>
          <Form.Label>
            Debug logging should only be enabled temporarily
          </Form.Label>
        </CommonFormGroup>
      </TitleBlock>
    );

    const analytics: JSX.Element = (
      <TitleBlock title="Analytics">
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
      </TitleBlock>
    );

    return (
      <Container fluid className="p-0">
        <CommonHeader>
          <CommonHeaderBtn
            iconProps={{ icon: faSave }}
            text="Save"
          ></CommonHeaderBtn>
        </CommonHeader>
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

export default connect()(SettingsGeneral);
