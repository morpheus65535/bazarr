import React, { FunctionComponent } from "react";

import {
  Check,
  CollapseBox,
  Group,
  Input,
  Message,
  Text,
  Selector,
  Slider,
  SettingsProvider,
} from "../components";

import { folderOptions, antiCaptchaOption, colorOptions } from "./options";

const SettingsSubtitlesView: FunctionComponent = () => {
  // TODO: Performance
  const subzeroOverride = (key: string) => {
    return (settings: SystemSettings) => {
      return settings.general.subzero_mods?.includes(key) ?? false;
    };
  };

  return (
    <SettingsProvider title="Subtitles - Bazarr (Settings)">
      <Group header="Subtitles Options">
        <CollapseBox>
          <CollapseBox.Control>
            <Input name="Subtitle Folder">
              <Selector
                options={folderOptions}
                settingKey="settings-general-subfolder"
              ></Selector>
              <Message type="info">
                Choose the folder you wish to store/read the subtitles
              </Message>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content on={(k) => k !== "" && k !== "current"}>
            <Input name="Custom Subtitles Folder">
              <Text settingKey="settings-general-subfolder_custom"></Text>
            </Input>
          </CollapseBox.Content>
        </CollapseBox>
        <CollapseBox>
          <CollapseBox.Control>
            <Input>
              <Check
                label="Upgrade Previously Downloaded Subtitles"
                settingKey="settings-general-upgrade_subs"
              ></Check>
              <Message type="info">
                Schedule a task to upgrade subtitles previously downloaded by
                Bazarr.
              </Message>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content>
            <Input>
              <Slider
                settingKey="settings-general-days_to_upgrade_subs"
                max={30}
              ></Slider>
              <Message type="info">
                Number of days to go back in history to upgrade subtitles
              </Message>
            </Input>
            <Input>
              <Check
                label="Upgrade Manually Downloaded Subtitles"
                settingKey="settings-general-upgrade_manual"
              ></Check>
              <Message type="info">
                Enable or disable upgrade of manually searched and downloaded
                subtitles.
              </Message>
            </Input>
          </CollapseBox.Content>
        </CollapseBox>
      </Group>
      <Group header="Anti-Captcha Options">
        <CollapseBox>
          <CollapseBox.Control>
            <Input>
              <Selector
                disabled
                settingKey="settings-general-anti_captcha_provider"
                options={antiCaptchaOption}
              ></Selector>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content on={(k) => k !== "" && k !== "none"}>
            <Input name="Provider"></Input>
          </CollapseBox.Content>
        </CollapseBox>
      </Group>
      <Group header="Performance / Optimization">
        <Input>
          <Check
            label="Adaptive Searching"
            settingKey="settings-general-adaptive_searching"
          ></Check>
          <Message type="info">
            When searching for subtitles, Bazarr will search less frequently to
            limit call to providers.
          </Message>
        </Input>
        <Input>
          <Check
            label="Search Enabled Providers Simultaneously"
            settingKey="settings-general-multithreading"
          ></Check>
          <Message type="info">
            Search multiple providers at once (Don't choose this on low powered
            devices)
          </Message>
        </Input>
        <CollapseBox>
          <CollapseBox.Control>
            <Input>
              <Check
                label="Use Embedded Subtitles"
                settingKey="settings-general-use_embedded_subs"
              ></Check>
              <Message type="info">
                Use embedded subtitles in media files when determining missing
                ones.
              </Message>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content>
            <Input>
              <Check
                label="Ignore Embedded PGS Subtitles"
                settingKey="settings-general-ignore_pgs_subs"
              ></Check>
              <Message type="info">
                Ignores PGS Subtitles in Embedded Subtitles detection.
              </Message>
            </Input>
            <Input>
              <Check
                label="Ignore Embedded VobSub Subtitles"
                settingKey="settings-general-ignore_vobsub_subs"
              ></Check>
              <Message type="info">
                Ignores VobSub Subtitles in Embedded Subtitles detection.
              </Message>
            </Input>
            <Input>
              <Check
                label="Show Only Desired Languages"
                settingKey="settings-general-embeddeenabled_providersd_subs_show_desired"
              ></Check>
              <Message type="info">
                Hide embedded subtitles for languages that are not currently
                desired.
              </Message>
            </Input>
          </CollapseBox.Content>
        </CollapseBox>
      </Group>
      <Group header="Post-Processing">
        <Input>
          <Check
            label="Encode Subtitles To UTF8"
            settingKey="settings-general-utf8_encode"
          ></Check>
          <Message type="info">
            Re-encode downloaded Subtitles to UTF8. Should be left enabled in
            most case.
          </Message>
        </Input>
        <Input>
          <Check
            label="Hearing Impaired"
            override={subzeroOverride("remove_HI")}
            settingKey="subzero-remove_HI"
          ></Check>
          <Message type="info">
            Removes tags, text and characters from subtitles that are meant for
            hearing impaired people.
          </Message>
        </Input>
        <Input>
          <Check
            label="Remove Tags"
            override={subzeroOverride("remove_tags")}
            settingKey="subzero-remove_tags"
          ></Check>
          <Message type="info">
            Removes all possible style tags from the subtitle, such as font,
            bold, color etc.
          </Message>
        </Input>
        <Input>
          <Check
            label="OCR Fixes"
            override={subzeroOverride("OCR_fixed")}
            settingKey="subzero-OCR_fixed"
          ></Check>
          <Message type="info">
            Fix issues that happen when a subtitle gets converted from bitmap to
            text through OCR.
          </Message>
        </Input>
        <Input>
          <Check
            label="Common Fixes"
            override={subzeroOverride("common")}
            settingKey="subzero-common"
          ></Check>
          <Message type="info">
            Fix common and whitespace/punctuation issues in subtitles.
          </Message>
        </Input>
        <Input>
          <Check
            label="Fix Uppercase"
            override={subzeroOverride("fix_uppercase")}
            settingKey="subzero-fix_uppercase"
          ></Check>
          <Message type="info">
            Tries to make subtitles that are completely uppercase readable.
          </Message>
        </Input>
        {/* TODO: Support Color Modification */}
        <CollapseBox>
          <CollapseBox.Control>
            <Input>
              <Check
                disabled
                label="Color"
                override={subzeroOverride("color")}
                settingKey="subzero-color"
              ></Check>
              <Message type="info">
                Adds color to your subtitles (for playback devices/software that
                don't ship their own color modes; only works for players that
                support color tags).
              </Message>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content>
            <Input>
              <Selector
                options={colorOptions}
                settingKey="subzero_color"
              ></Selector>
            </Input>
          </CollapseBox.Content>
        </CollapseBox>
        <Input>
          <Check
            label="Reverse RTL"
            override={subzeroOverride("reverse_rtl")}
            settingKey="subzero-reverse_rtl"
          ></Check>
          <Message type="info">
            Reverses the punctuation in right-to-left subtitles for problematic
            playback devices.
          </Message>
        </Input>
        <CollapseBox>
          <CollapseBox.Control>
            <Input>
              <Check
                label="Permission (chmod)"
                settingKey="settings-general-chmod_enabled"
              ></Check>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content>
            <Input>
              <Text
                placeholder="0777"
                settingKey="settings-general-chmod"
              ></Text>
              <Message type="info">Must be 4 digit octal</Message>
            </Input>
          </CollapseBox.Content>
        </CollapseBox>
        <CollapseBox>
          <CollapseBox.Control>
            <Input>
              <Check
                label="Automatic Subtitles Synchronization"
                settingKey="settings-subsync-use_subsync"
              ></Check>
              <Message type="info">
                Enable the automatic subtitles synchronization after downloading
                a subtitles.
              </Message>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content>
            <Input>
              <Check label="Debug" settingKey="settings-subsync-debug"></Check>
              <Message type="info">
                Do not actually sync the subtitles but generate a .tar.gz file
                to be able to open an issue for ffsubsync. This file will reside
                alongside the media file.
              </Message>
            </Input>
            <CollapseBox>
              <CollapseBox.Control>
                <Input>
                  <Check
                    label="Series Score Threshold"
                    settingKey="settings-subsync-use_subsync_threshold"
                  ></Check>
                </Input>
              </CollapseBox.Control>
              <CollapseBox.Content indent={false}>
                <Input>
                  <Slider settingKey="settings-subsync-subsync_threshold"></Slider>
                </Input>
              </CollapseBox.Content>
            </CollapseBox>
            <CollapseBox>
              <CollapseBox.Control>
                <Input>
                  <Check
                    label="Movies Score Threshold"
                    settingKey="settings-subsync-use_subsync_movie_threshold"
                  ></Check>
                </Input>
              </CollapseBox.Control>
              <CollapseBox.Content indent={false}>
                <Input>
                  <Slider settingKey="settings-subsync-subsync_movie_threshold"></Slider>
                </Input>
              </CollapseBox.Content>
            </CollapseBox>
          </CollapseBox.Content>
        </CollapseBox>
        <Input>
          {/* TODO: Implementation */}
          <Check
            disabled
            settingKey="settings-general-postprocessing_cmd"
            label="Use Custom Post-Processing"
          ></Check>
          <Message type="info">
            Enable the post-processing execution after downloading a subtitles.
          </Message>
        </Input>
      </Group>
    </SettingsProvider>
  );
};

export default SettingsSubtitlesView;
