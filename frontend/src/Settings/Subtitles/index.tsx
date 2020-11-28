import React from "react";
import { Container, Form } from "react-bootstrap";
import { connect } from "react-redux";
import {} from "../../redux/actions/system";

import TitleBlock from "../../components/TitleBlock";
import { CommonHeader, CommonHeaderBtn } from "../../components/CommonHeader";
import { CommonFormGroup } from "../../components/CommonForm";

import { faSave } from "@fortawesome/free-solid-svg-icons";

interface Props {}

interface State {
  upgradeEnabled: boolean;
  antiCaptchaSelection: string;
}

// function mapStateToProps({ system }: StoreState) {
//   return {
//     languages: system.languages.items,
//     enabled: system.enabledLanguage,
//   };
// }

const formControlClass = "w-50";

const SubtitleFolderOption = [
  ["current", "AlongSide Media File"],
  ["relative", "Relative Path to Media File"],
  ["absolute", "Absolute Path"],
];

const AntiCaptchaOption = [
  ["none", "None"],
  ["anticaptcha", "Anti-Captcha"],
  ["deathbycaptcha", "Death by Captcha"],
];

class SettingsSubtitlesView extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      upgradeEnabled: false,
      antiCaptchaSelection: "none",
    };
  }

  onUpgradeChanged(val: boolean) {
    this.setState({
      ...this.state,
      upgradeEnabled: val,
    });
  }

  onProviderChanged(val: string) {
    this.setState({
      ...this.state,
      antiCaptchaSelection: val,
    });
  }

  renderAcProvider(): JSX.Element {
    const { antiCaptchaSelection } = this.state;

    if (antiCaptchaSelection === "anticaptcha") {
      return (
        <div>
          <CommonFormGroup title="Provider Website">
            <a
              className="m-0 p-0"
              href="http://getcaptchasolution.com/eixxo1rsnw"
              target="_blank"
              rel="noopener noreferrer"
            >
              Anti-Captcha.com
            </a>
          </CommonFormGroup>
          <CommonFormGroup title="Account Key">
            <Form.Control
              type="text"
              className={formControlClass}
            ></Form.Control>
          </CommonFormGroup>
        </div>
      );
    } else if (antiCaptchaSelection === "deathbycaptcha") {
      return (
        <div>
          <CommonFormGroup title="Provider Website">
            <a
              className="m-0 p-0"
              href="https://www.deathbycaptcha.com/"
              target="_blank"
              rel="noopener noreferrer"
            >
              DeathByCaptcha.com
            </a>
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
          </CommonFormGroup>
        </div>
      );
    } else {
      return <div></div>;
    }
  }

  render(): JSX.Element {
    const { upgradeEnabled } = this.state;
    const subtitles: JSX.Element = (
      <TitleBlock title="Subtitles Options">
        <CommonFormGroup title="Subtitle Folder">
          <Form.Control as="select" className={formControlClass}>
            {SubtitleFolderOption.map((val, idx) => (
              <option key={idx} value={val[0]}>
                {val[1]}
              </option>
            ))}
          </Form.Control>
          <Form.Label>
            Choose the folder you wish to store/read the subtitles
          </Form.Label>
        </CommonFormGroup>
        <CommonFormGroup title="Upgrade Previously Downloaded subtitles">
          <Form.Check
            type="checkbox"
            className={formControlClass}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              this.onUpgradeChanged(event.target.checked);
            }}
          ></Form.Check>
          <Form.Label>
            Schedule a task to upgrade subtitles previously downloaded by
            Bazarr.
          </Form.Label>
        </CommonFormGroup>
        <div hidden={!upgradeEnabled}>
          <CommonFormGroup title="Number of days to go back in history to upgrade subtitles">
            <Form.Control
              className={formControlClass}
              type="range"
              min={0}
              max={30}
            ></Form.Control>
          </CommonFormGroup>
          <CommonFormGroup title="Upgrade Manually Downloaded subtitles">
            <Form.Check
              className={formControlClass}
              type="checkbox"
            ></Form.Check>
            <Form.Label>
              Enable or disable upgrade of manually searched and downloaded
              subtitles.
            </Form.Label>
          </CommonFormGroup>
        </div>
      </TitleBlock>
    );

    const anti_captcha: JSX.Element = (
      <TitleBlock title="Anti-Captcha Options">
        <CommonFormGroup title="Provider">
          <Form.Control
            as="select"
            className={formControlClass}
            onChange={(event) => {
              this.onProviderChanged(event.target.value);
            }}
          >
            {AntiCaptchaOption.map((val, idx) => (
              <option key={idx} value={val[0]}>
                {val[1]}
              </option>
            ))}
          </Form.Control>
          <Form.Label>
            Choose the Anti-Captcha provider you want to use.
          </Form.Label>
        </CommonFormGroup>
        {this.renderAcProvider()}
      </TitleBlock>
    );

    const performance: JSX.Element = (
      <TitleBlock title="Performance / Optimization">
        <CommonFormGroup title="Adaptive Searching">
          <Form.Check className={formControlClass} type="checkbox"></Form.Check>
          <Form.Label>
            When searching for subtitles, Bazarr will search less frequently to
            limit call to providers.
          </Form.Label>
        </CommonFormGroup>
        <CommonFormGroup title="Search Enabled Providers Simultaneously">
          <Form.Check className={formControlClass} type="checkbox"></Form.Check>
          <Form.Label>
            Search multiple providers at once (Don't choose this on low powered
            devices)
          </Form.Label>
        </CommonFormGroup>
        <CommonFormGroup title="Use Embedded Subtitles">
          <Form.Check className={formControlClass} type="checkbox"></Form.Check>
          <Form.Label>
            Use embedded subtitles in media files when determining missing ones.
          </Form.Label>
        </CommonFormGroup>
      </TitleBlock>
    );

    return (
      <Container fluid className="p-0">
        <CommonHeader>
          <CommonHeaderBtn iconProps={{ icon: faSave }}>Save</CommonHeaderBtn>
        </CommonHeader>
        <Form className="p-4">
          {subtitles}
          {anti_captcha}
          {performance}
        </Form>
      </Container>
    );
  }
}

export default connect(null, {})(SettingsSubtitlesView);
