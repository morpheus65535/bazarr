import React from "react";
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
  CollapseBox,
  Group,
  Input,
  Message,
  Select,
  Slider,
} from "../Components";

import { faSave } from "@fortawesome/free-solid-svg-icons";

interface Props {
  settings: AsyncState<SystemSettings | undefined>;
}

function mapStateToProps({ system }: StoreState) {
  return {
    settings: system.settings,
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

    return (
      <AsyncStateOverlay state={settings}>
        {(item) => (
          <Container fluid>
            <Helmet>
              <title>Subtitles - Bazarr (Settings)</title>
            </Helmet>
            <Row>
              <ContentHeader>
                <ContentHeaderButton icon={faSave}>Save</ContentHeaderButton>
              </ContentHeader>
            </Row>
            <Row>
              <Container className="p-4">
                <Group header="Subtitles Options">
                  <Input name="Subtitle Folder">
                    <Select
                      options={folderOptions}
                      defaultKey={item.general.subfolder}
                    ></Select>
                    <Message type="info">
                      Choose the folder you wish to store/read the subtitles
                    </Message>
                  </Input>
                  <CollapseBox
                    indent
                    defaultOpen={item.general.upgrade_subs}
                    control={(change) => (
                      <Input>
                        <Check
                          label="Upgrade Previously Downloaded subtitles"
                          defaultValue={item.general.upgrade_subs}
                          onChange={(val) => {
                            change(val);
                          }}
                        ></Check>
                        <Message type="info">
                          Schedule a task to upgrade subtitles previously
                          downloaded by Bazarr.
                        </Message>
                      </Input>
                    )}
                  >
                    <Input>
                      <Slider></Slider>
                      <Message type="info">
                        Number of days to go back in history to upgrade
                        subtitles
                      </Message>
                    </Input>
                    <Input>
                      <Check
                        label="Upgrade Manually Downloaded subtitles"
                        defaultValue={item.general.upgrade_manual}
                      ></Check>
                      <Message type="info">
                        Enable or disable upgrade of manually searched and
                        downloaded subtitles.
                      </Message>
                    </Input>
                  </CollapseBox>
                </Group>
                <Group header="Anti-Captcha Options">
                  <CollapseBox
                    indent
                    control={(change) => (
                      <Input>
                        <Select
                          options={antiCaptchaOption}
                          nullKey="none"
                          onChange={(val) => {
                            change(val !== "none");
                          }}
                        ></Select>
                      </Input>
                    )}
                  >
                    <Input name="Provider"></Input>
                  </CollapseBox>
                </Group>
                <Group header="Performance / Optimization">
                  <Input>
                    <Check
                      label="Adaptive Searching"
                      defaultValue={item.general.adaptive_searching}
                    ></Check>
                    <Message type="info">
                      When searching for subtitles, Bazarr will search less
                      frequently to limit call to providers.
                    </Message>
                  </Input>
                  <Input>
                    <Check label="Search Enabled Providers Simultaneously"></Check>
                    <Message type="info">
                      Search multiple providers at once (Don't choose this on
                      low powered devices)
                    </Message>
                  </Input>
                  <CollapseBox
                    indent
                    defaultOpen={item.general.use_embedded_subs}
                    control={(change) => (
                      <Input>
                        <Check
                          label="Use Embedded Subtitles"
                          defaultValue={item.general.use_embedded_subs}
                          onChange={(val) => {
                            change(val);
                          }}
                        ></Check>
                        <Message type="info">
                          Use embedded subtitles in media files when determining
                          missing ones.
                        </Message>
                      </Input>
                    )}
                  >
                    <Input>
                      <Check
                        label="Ignore Embedded PGS Subtitles"
                        defaultValue={item.general.ignore_pgs_subs}
                      ></Check>
                      <Message type="info">
                        Ignores PGS Subtitles in Embedded Subtitles detection.
                      </Message>
                    </Input>
                    <Input>
                      <Check
                        label="Ignore Embedded VobSub Subtitles"
                        defaultValue={item.general.ignore_vobsub_subs}
                      ></Check>
                      <Message type="info">
                        Ignores VobSub Subtitles in Embedded Subtitles
                        detection.
                      </Message>
                    </Input>
                    <Input>
                      <Check
                        label="Show Only Desired Languages"
                        defaultValue={
                          item.general
                            .embeddeenabled_providersd_subs_show_desired
                        }
                      ></Check>
                      <Message type="info">
                        Hide embedded subtitles for languages that are not
                        currently desired.
                      </Message>
                    </Input>
                  </CollapseBox>
                </Group>
                <Group header="Post-Processing">
                  <Input>
                    <Check label="Encode Subtitles To UTF8"></Check>
                    <Message type="info">
                      Re-encode downloaded Subtitles to UTF8. Should be left
                      enabled in most case.
                    </Message>
                  </Input>
                  <Input>
                    <Check label="Hearing Impaired"></Check>
                    <Message type="info">
                      Removes tags, text and characters from subtitles that are
                      meant for hearing impaired people.
                    </Message>
                  </Input>
                  <Input>
                    <Check label="Remove Tags"></Check>
                    <Message type="info">
                      Removes all possible style tags from the subtitle, such as
                      font, bold, color etc.
                    </Message>
                  </Input>
                  <Input>
                    <Check label="OCR Fixes"></Check>
                    <Message type="info">
                      Fix issues that happen when a subtitle gets converted from
                      bitmap to text through OCR.
                    </Message>
                  </Input>
                  <Input>
                    <Check label="Remove Tags"></Check>
                    <Message type="info">
                      Removes all possible style tags from the subtitle, such as
                      font, bold, color etc.
                    </Message>
                  </Input>
                  <Input>
                    <Check label="Common Fixes"></Check>
                    <Message type="info">
                      Fix common and whitespace/punctuation issues in subtitles.
                    </Message>
                  </Input>
                  <Input>
                    <Check label="Fix Uppercase"></Check>
                    <Message type="info">
                      Tries to make subtitles that are completely uppercase
                      readable.
                    </Message>
                  </Input>
                  <Input>
                    <Check label="Color"></Check>
                    <Message type="info">
                      Adds color to your subtitles (for playback
                      devices/software that don't ship their own color modes;
                      only works for players that support color tags).
                    </Message>
                  </Input>
                  <Input>
                    <Check label="Reverse RTL"></Check>
                    <Message type="info">
                      Reverses the punctuation in right-to-left subtitles for
                      problematic playback devices.
                    </Message>
                  </Input>
                  <Input>
                    <Check label="Permission (chmod)"></Check>
                  </Input>
                  <Input>
                    <Check label="Automatic Subtitles Synchronization"></Check>
                    <Message type="info">
                      Enable the automatic subtitles synchronization after
                      downloading a subtitles.
                    </Message>
                  </Input>
                  <Input>
                    <Check label="Use Custom Post-Processing"></Check>
                    <Message type="info">
                      Enable the post-processing execution after downloading a
                      subtitles.
                    </Message>
                  </Input>
                </Group>
              </Container>
            </Row>
          </Container>
        )}
      </AsyncStateOverlay>
    );
  }
}

export default connect(mapStateToProps, {})(SettingsSubtitlesView);
