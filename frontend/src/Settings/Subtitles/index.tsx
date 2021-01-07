import React from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import {
  ContentHeader,
  ContentHeaderButton,
  LoadingIndicator,
} from "../../Components";

import { Check, Group, Input, Message, Select } from "../Components";

import { faSave } from "@fortawesome/free-solid-svg-icons";

interface Props {
  settings?: SystemSettings;
}

function mapStateToProps({ system }: StoreState) {
  return {
    settings: system.settings.items,
  };
}

const folderOptions = {
  current: "AlongSide Media File",
  relative: "Relative Path to Media File",
  absolute: "Absolute Path",
};

const antiCaptchaOption = {
  none: "None",
  anticaptcha: "Anti-Captcha",
  deathbycaptcha: "Death by Captcha",
};

class SettingsSubtitlesView extends React.Component<Props> {
  render(): JSX.Element {
    const { settings } = this.props;

    if (settings === undefined) {
      return <LoadingIndicator></LoadingIndicator>;
    }

    const general = settings.general;

    return (
      <Container fluid>
        <Helmet>
          <title>Subtitles - Bazarr (Settings)</title>
        </Helmet>
        <Row>
          <ContentHeader>
            <ContentHeaderButton icon={faSave}>Save</ContentHeaderButton>
          </ContentHeader>
        </Row>
        <Row className="p-4">
          <Container>
            <Group header="Subtitles Options">
              <Input name="Subtitle Folder">
                <Select
                  options={folderOptions}
                  defaultKey={general.subfolder}
                ></Select>
                <Message type="info">
                  Choose the folder you wish to store/read the subtitles
                </Message>
              </Input>
              <Input>
                <Check
                  label="Upgrade Previously Downloaded subtitles"
                  defaultValue={general.upgrade_subs}
                ></Check>
                <Message type="info">
                  Schedule a task to upgrade subtitles previously downloaded by
                  Bazarr.
                </Message>
              </Input>
              <Input>
                <Check
                  label="Upgrade Manually Downloaded subtitles"
                  defaultValue={general.upgrade_manual}
                ></Check>
                <Message type="info">
                  Enable or disable upgrade of manually searched and downloaded
                  subtitles.
                </Message>
              </Input>
            </Group>
            <Group header="Anti-Captcha Options">
              <Input>
                <Select options={antiCaptchaOption} nullKey="none"></Select>
              </Input>
            </Group>
            <Group header="Performance / Optimization">
              <Input>
                <Check
                  label="Adaptive Searching"
                  defaultValue={general.adaptive_searching}
                ></Check>
                <Message type="info">
                  When searching for subtitles, Bazarr will search less
                  frequently to limit call to providers.
                </Message>
              </Input>
              <Input>
                <Check label="Search Enabled Providers Simultaneously"></Check>
                <Message type="info">
                  Search multiple providers at once (Don't choose this on low
                  powered devices)
                </Message>
              </Input>
              <Input>
                <Check
                  label="Use Embedded Subtitles"
                  defaultValue={general.use_embedded_subs}
                ></Check>
                <Message type="info">
                  Use embedded subtitles in media files when determining missing
                  ones.
                </Message>
              </Input>
            </Group>
          </Container>
        </Row>
      </Container>
    );
  }
}

export default connect(mapStateToProps, {})(SettingsSubtitlesView);
