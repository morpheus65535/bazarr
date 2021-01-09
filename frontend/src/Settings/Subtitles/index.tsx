import React, { FunctionComponent } from "react";
import { Container } from "react-bootstrap";
import { connect } from "react-redux";

import {
  Check,
  CollapseBox,
  Group,
  Input,
  Message,
  Text,
  Select,
  Slider,
} from "../Components";

import SettingTemplate from "../Components/template";

interface Props {}

function mapStateToProps({ system }: StoreState) {
  return {};
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

const colorOptions = {
  white: "White",
  lightgray: "Light Gray",
};

const SettingsSubtitlesView: FunctionComponent<Props> = (props) => {
  return (
    <SettingTemplate title="Subtitles - Bazarr (Settings)">
      {(settings, update) => (
        <Container className="p-4">
          <Group header="Subtitles Options">
            <CollapseBox
              indent
              defaultOpen={settings.general.subfolder !== "current"}
              control={(change) => (
                <Input name="Subtitle Folder">
                  <Select
                    options={folderOptions}
                    remoteKey="settings-general-subfolder"
                    defaultKey={settings.general.subfolder}
                    onChange={(v, k) => {
                      change(v !== "current");
                      update(v, k);
                    }}
                  ></Select>
                  <Message type="info">
                    Choose the folder you wish to store/read the subtitles
                  </Message>
                </Input>
              )}
            >
              <Input name="Custom Subtitles Folder">
                <Text remoteKey="settings-general-subfolder_custom"></Text>
              </Input>
            </CollapseBox>
            <CollapseBox
              indent
              defaultOpen={settings.general.upgrade_subs}
              control={(change) => (
                <Input>
                  <Check
                    label="Upgrade Previously Downloaded subtitles"
                    remoteKey="settings-general-upgrade_subs"
                    defaultValue={settings.general.upgrade_subs}
                    onChange={(v, k) => {
                      change(v);
                      update(v, k);
                    }}
                  ></Check>
                  <Message type="info">
                    Schedule a task to upgrade subtitles previously downloaded
                    by Bazarr.
                  </Message>
                </Input>
              )}
            >
              <Input>
                <Slider></Slider>
                <Message type="info">
                  Number of days to go back in history to upgrade subtitles
                </Message>
              </Input>
              <Input>
                <Check
                  label="Upgrade Manually Downloaded subtitles"
                  remoteKey="settings-general-upgrade_manual"
                  defaultValue={settings.general.upgrade_manual}
                  onChange={update}
                ></Check>
                <Message type="info">
                  Enable or disable upgrade of manually searched and downloaded
                  subtitles.
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
                    remoteKey="settings-general-anti_captcha_provider"
                    onChange={(v, k) => {
                      change(v !== "none");
                      update(v, k);
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
                remoteKey="settings-general-adaptive_searching"
                defaultValue={settings.general.adaptive_searching}
                onChange={update}
              ></Check>
              <Message type="info">
                When searching for subtitles, Bazarr will search less frequently
                to limit call to providers.
              </Message>
            </Input>
            <Input>
              <Check
                label="Search Enabled Providers Simultaneously"
                remoteKey="settings-general-multithreading"
                defaultValue={settings.general.multithreading}
                onChange={update}
              ></Check>
              <Message type="info">
                Search multiple providers at once (Don't choose this on low
                powered devices)
              </Message>
            </Input>
            <CollapseBox
              indent
              defaultOpen={settings.general.use_embedded_subs}
              control={(change) => (
                <Input>
                  <Check
                    label="Use Embedded Subtitles"
                    remoteKey="settings-general-use_embedded_subs"
                    defaultValue={settings.general.use_embedded_subs}
                    onChange={(v, k) => {
                      change(v);
                      update(v, k);
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
                  remoteKey="settings-general-ignore_pgs_subs"
                  defaultValue={settings.general.ignore_pgs_subs}
                  onChange={update}
                ></Check>
                <Message type="info">
                  Ignores PGS Subtitles in Embedded Subtitles detection.
                </Message>
              </Input>
              <Input>
                <Check
                  label="Ignore Embedded VobSub Subtitles"
                  remoteKey="settings-general-ignore_vobsub_subs"
                  defaultValue={settings.general.ignore_vobsub_subs}
                  onChange={update}
                ></Check>
                <Message type="info">
                  Ignores VobSub Subtitles in Embedded Subtitles detection.
                </Message>
              </Input>
              <Input>
                <Check
                  label="Show Only Desired Languages"
                  remoteKey="settings-general-embeddeenabled_providersd_subs_show_desired"
                  defaultValue={
                    settings.general.embeddeenabled_providersd_subs_show_desired
                  }
                  onChange={update}
                ></Check>
                <Message type="info">
                  Hide embedded subtitles for languages that are not currently
                  desired.
                </Message>
              </Input>
            </CollapseBox>
          </Group>
          <Group header="Post-Processing">
            <Input>
              <Check
                label="Encode Subtitles To UTF8"
                remoteKey="settings-general-utf8_encode"
                defaultValue={settings.general.utf8_encode}
                onChange={update}
              ></Check>
              <Message type="info">
                Re-encode downloaded Subtitles to UTF8. Should be left enabled
                in most case.
              </Message>
            </Input>
            <Input>
              <Check
                remoteKey="remove_HI"
                label="Hearing Impaired"
                defaultValue={settings.general.subzero_mods.includes(
                  "remove_HI"
                )}
                onChange={update}
              ></Check>
              <Message type="info">
                Removes tags, text and characters from subtitles that are meant
                for hearing impaired people.
              </Message>
            </Input>
            <Input>
              <Check
                remoteKey="remove_tags"
                label="Remove Tags"
                defaultValue={settings.general.subzero_mods.includes(
                  "remove_tags"
                )}
                onChange={update}
              ></Check>
              <Message type="info">
                Removes all possible style tags from the subtitle, such as font,
                bold, color etc.
              </Message>
            </Input>
            <Input>
              <Check
                remoteKey="OCR_fixed"
                label="OCR Fixes"
                defaultValue={settings.general.subzero_mods.includes(
                  "ocr_fixed"
                )}
                onChange={update}
              ></Check>
              <Message type="info">
                Fix issues that happen when a subtitle gets converted from
                bitmap to text through OCR.
              </Message>
            </Input>
            <Input>
              <Check
                remoteKey="common"
                label="Common Fixes"
                defaultValue={settings.general.subzero_mods.includes("common")}
                onChange={update}
              ></Check>
              <Message type="info">
                Fix common and whitespace/punctuation issues in subtitles.
              </Message>
            </Input>
            <Input>
              <Check
                remoteKey="fix_uppercase"
                label="Fix Uppercase"
                defaultValue={settings.general.subzero_mods.includes(
                  "fix_uppercase"
                )}
              ></Check>
              <Message type="info">
                Tries to make subtitles that are completely uppercase readable.
              </Message>
            </Input>
            <CollapseBox
              indent
              control={(change) => (
                <Input>
                  <Check
                    label="Color"
                    remoteKey="subzero_color_enabled"
                    onChange={(v, k) => {
                      change(v);
                      update(v, k);
                    }}
                  ></Check>
                  <Message type="info">
                    Adds color to your subtitles (for playback devices/software
                    that don't ship their own color modes; only works for
                    players that support color tags).
                  </Message>
                </Input>
              )}
            >
              <Input>
                <Select
                  options={colorOptions}
                  remoteKey="subzero_color"
                  onChange={update}
                  defaultKey="white"
                ></Select>
              </Input>
            </CollapseBox>
            <Input>
              <Check
                remoteKey="reverse_rtl"
                label="Reverse RTL"
                defaultValue={settings.general.subzero_mods.includes(
                  "reverse_rtl"
                )}
              ></Check>
              <Message type="info">
                Reverses the punctuation in right-to-left subtitles for
                problematic playback devices.
              </Message>
            </Input>
            <CollapseBox
              indent
              defaultOpen={settings.general.chmod_enabled}
              control={(change) => (
                <Input>
                  <Check
                    remoteKey="settings-general-chmod_enabled"
                    defaultValue={settings.general.chmod_enabled}
                    label="Permission (chmod)"
                    onChange={(v, k) => {
                      change(v);
                      update(v, k);
                    }}
                  ></Check>
                </Input>
              )}
            >
              <Input>
                <Text
                  placeholder="0777"
                  remoteKey="settings-general-chmod"
                  defaultValue={settings.general.chmod}
                  onChange={update}
                ></Text>
                <Message type="info">Must be 4 digit octal</Message>
              </Input>
            </CollapseBox>
            <Input>
              <Check
                label="Automatic Subtitles Synchronization"
                remoteKey="settings-subsync-use_subsync"
                defaultValue={settings.subsync.use_subsync}
                onChange={update}
              ></Check>
              <Message type="info">
                Enable the automatic subtitles synchronization after downloading
                a subtitles.
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
      )}
    </SettingTemplate>
  );
};

export default connect(mapStateToProps, {})(SettingsSubtitlesView);
