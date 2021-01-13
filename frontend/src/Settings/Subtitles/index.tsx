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
  Selector,
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
        <Container>
          <Group header="Subtitles Options">
            <CollapseBox
              indent
              defaultOpen={settings.general.subfolder !== "current"}
              control={(change) => (
                <Input name="Subtitle Folder">
                  <Selector
                    options={folderOptions}
                    defaultKey={settings.general.subfolder}
                    onSelect={(v: string) => {
                      change(v !== "current");
                      update(v, "settings-general-subfolder");
                    }}
                  ></Selector>
                  <Message type="info">
                    Choose the folder you wish to store/read the subtitles
                  </Message>
                </Input>
              )}
            >
              <Input name="Custom Subtitles Folder">
                <Text
                  onChange={(v) =>
                    update(v, "settings-general-subfolder_custom")
                  }
                ></Text>
              </Input>
            </CollapseBox>
            <CollapseBox
              indent
              defaultOpen={settings.general.upgrade_subs}
              control={(change) => (
                <Input>
                  <Check
                    label="Upgrade Previously Downloaded subtitles"
                    defaultValue={settings.general.upgrade_subs}
                    onChange={(v) => {
                      change(v);
                      update(v, "settings-general-upgrade_subs");
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
                  defaultValue={settings.general.upgrade_manual}
                  onChange={(v) => update(v, "settings-general-upgrade_manual")}
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
                  <Selector
                    disabled
                    options={antiCaptchaOption}
                    nullKey="none"
                    onSelect={(v: string) => {
                      change(v !== "none");
                      update(v, "settings-general-anti_captcha_provider");
                    }}
                  ></Selector>
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
                defaultValue={settings.general.adaptive_searching}
                onChange={(v) =>
                  update(v, "settings-general-adaptive_searching")
                }
              ></Check>
              <Message type="info">
                When searching for subtitles, Bazarr will search less frequently
                to limit call to providers.
              </Message>
            </Input>
            <Input>
              <Check
                label="Search Enabled Providers Simultaneously"
                defaultValue={settings.general.multithreading}
                onChange={(v) => update(v, "settings-general-multithreading")}
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
                    defaultValue={settings.general.use_embedded_subs}
                    onChange={(v) => {
                      change(v);
                      update(v, "settings-general-use_embedded_subs");
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
                  defaultValue={settings.general.ignore_pgs_subs}
                  onChange={(v) =>
                    update(v, "settings-general-ignore_pgs_subs")
                  }
                ></Check>
                <Message type="info">
                  Ignores PGS Subtitles in Embedded Subtitles detection.
                </Message>
              </Input>
              <Input>
                <Check
                  label="Ignore Embedded VobSub Subtitles"
                  defaultValue={settings.general.ignore_vobsub_subs}
                  onChange={(v) =>
                    update(v, "settings-general-ignore_vobsub_subs")
                  }
                ></Check>
                <Message type="info">
                  Ignores VobSub Subtitles in Embedded Subtitles detection.
                </Message>
              </Input>
              <Input>
                <Check
                  label="Show Only Desired Languages"
                  defaultValue={
                    settings.general.embeddeenabled_providersd_subs_show_desired
                  }
                  onChange={(v) =>
                    update(
                      v,
                      "settings-general-embeddeenabled_providersd_subs_show_desired"
                    )
                  }
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
                defaultValue={settings.general.utf8_encode}
                onChange={(v) => update(v, "settings-general-utf8_encode")}
              ></Check>
              <Message type="info">
                Re-encode downloaded Subtitles to UTF8. Should be left enabled
                in most case.
              </Message>
            </Input>
            <Input>
              <Check
                label="Hearing Impaired"
                defaultValue={settings.general.subzero_mods.includes(
                  "remove_HI"
                )}
                onChange={(v) => update(v, "remove_HI")}
              ></Check>
              <Message type="info">
                Removes tags, text and characters from subtitles that are meant
                for hearing impaired people.
              </Message>
            </Input>
            <Input>
              <Check
                label="Remove Tags"
                defaultValue={settings.general.subzero_mods.includes(
                  "remove_tags"
                )}
                onChange={(v) => update(v, "remove_tags")}
              ></Check>
              <Message type="info">
                Removes all possible style tags from the subtitle, such as font,
                bold, color etc.
              </Message>
            </Input>
            <Input>
              <Check
                label="OCR Fixes"
                defaultValue={settings.general.subzero_mods.includes(
                  "ocr_fixed"
                )}
                onChange={(v) => update(v, "OCR_fixed")}
              ></Check>
              <Message type="info">
                Fix issues that happen when a subtitle gets converted from
                bitmap to text through OCR.
              </Message>
            </Input>
            <Input>
              <Check
                label="Common Fixes"
                defaultValue={settings.general.subzero_mods.includes("common")}
                onChange={(v) => update(v, "common")}
              ></Check>
              <Message type="info">
                Fix common and whitespace/punctuation issues in subtitles.
              </Message>
            </Input>
            <Input>
              <Check
                label="Fix Uppercase"
                defaultValue={settings.general.subzero_mods.includes(
                  "fix_uppercase"
                )}
                onChange={(v) => update(v, "fix_uppercase")}
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
                    onChange={(v) => {
                      change(v);
                      update(v, "subzero_color_enabled");
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
                <Selector
                  options={colorOptions}
                  onSelect={(v: string) => update(v, "subzero_color")}
                  defaultKey="white"
                ></Selector>
              </Input>
            </CollapseBox>
            <Input>
              <Check
                label="Reverse RTL"
                defaultValue={settings.general.subzero_mods.includes(
                  "reverse_rtl"
                )}
                onChange={(v) => update(v, "reverse_rtl")}
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
                    defaultValue={settings.general.chmod_enabled}
                    label="Permission (chmod)"
                    onChange={(v) => {
                      change(v);
                      update(v, "settings-general-chmod_enabled");
                    }}
                  ></Check>
                </Input>
              )}
            >
              <Input>
                <Text
                  placeholder="0777"
                  defaultValue={settings.general.chmod}
                  onChange={(v) => update(v, "settings-general-chmod")}
                ></Text>
                <Message type="info">Must be 4 digit octal</Message>
              </Input>
            </CollapseBox>
            <Input>
              <Check
                label="Automatic Subtitles Synchronization"
                defaultValue={settings.subsync.use_subsync}
                onChange={(v) => update(v, "settings-subsync-use_subsync")}
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
