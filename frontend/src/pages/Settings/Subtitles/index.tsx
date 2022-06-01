import { Anchor } from "@mantine/core";
import { FunctionComponent } from "react";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Password,
  Section,
  Selector,
  Slider,
  Text,
} from "../components";
import {
  adaptiveSearchingDelayOption,
  adaptiveSearchingDeltaOption,
  antiCaptchaOption,
  colorOptions,
  folderOptions,
  hiExtensionOptions,
} from "./options";

const subzeroOverride = (key: string) => {
  return (settings: Settings) => {
    return settings.general.subzero_mods?.includes(key) ?? false;
  };
};

const subzeroColorOverride = (settings: Settings) => {
  return (
    settings.general.subzero_mods?.find((v) => v.startsWith("color")) ?? ""
  );
};

const SettingsSubtitlesView: FunctionComponent = () => {
  return (
    <Layout name="Subtitles">
      <Section header="Subtitles Options">
        <Selector
          label="Subtitle Folder"
          options={folderOptions}
          settingKey="settings-general-subfolder"
        ></Selector>
        <Message>
          Choose the folder you wish to store/read the subtitles
        </Message>
        <CollapseBox
          settingKey="settings-general-subfolder"
          on={(k) => k !== "" && k !== "current"}
        >
          <Text
            label="Custom Subtitles Folder"
            settingKey="settings-general-subfolder_custom"
          ></Text>
        </CollapseBox>
        <Check
          label="Upgrade Previously Downloaded Subtitles"
          settingKey="settings-general-upgrade_subs"
        ></Check>
        <Message>
          Schedule a task to upgrade subtitles previously downloaded by Bazarr.
        </Message>
        <CollapseBox settingKey="settings-general-upgrade_subs">
          <Slider
            settingKey="settings-general-days_to_upgrade_subs"
            max={30}
            mb="lg"
          ></Slider>
          <Message>
            Number of days to go back in history to upgrade subtitles
          </Message>
          <Check
            label="Upgrade Manually Downloaded or Translated Subtitles"
            settingKey="settings-general-upgrade_manual"
          ></Check>
          <Message>
            Enable or disable upgrade of manually downloaded or translated
            subtitles.
          </Message>
        </CollapseBox>
        <Selector
          label="Hearing-impaired subtitles extension"
          options={hiExtensionOptions}
          settingKey="settings-general-hi_extension"
        ></Selector>
        <Message>
          What file extension to use when saving hearing-impaired subtitles to
          disk (e.g., video.en.sdh.srt).
        </Message>
      </Section>
      <Section header="Anti-Captcha Options">
        <Selector
          clearable
          placeholder="Select a provider"
          settingKey="settings-general-anti_captcha_provider"
          beforeStaged={(v) => (v === undefined ? "None" : v)}
          options={antiCaptchaOption}
        ></Selector>
        <Message>Choose the anti-captcha provider you want to use</Message>
        <CollapseBox
          settingKey="settings-general-anti_captcha_provider"
          on={(value) => value === "anti-captcha"}
        >
          <Anchor href="http://getcaptchasolution.com/eixxo1rsnw">
            Anti-Captcha.com
          </Anchor>
          <Text
            label="Account Key"
            settingKey="settings-anticaptcha-anti_captcha_key"
          ></Text>
        </CollapseBox>
        <CollapseBox
          settingKey="settings-general-anti_captcha_provider"
          on={(value) => value === "death-by-captcha"}
        >
          <Anchor href="https://www.deathbycaptcha.com">
            DeathByCaptcha.com
          </Anchor>
          <Text
            label="Username"
            settingKey="settings-deathbycaptcha-username"
          ></Text>
          <Password
            label="Password"
            settingKey="settings-deathbycaptcha-password"
          ></Password>
        </CollapseBox>
      </Section>
      <Section header="Performance / Optimization">
        <Check
          label="Adaptive Searching"
          settingKey="settings-general-adaptive_searching"
        ></Check>
        <Message>
          When searching for subtitles, Bazarr will reduce search frequency to
          limit call to providers.
        </Message>
        <CollapseBox settingKey="settings-general-adaptive_searching">
          <Selector
            settingKey="settings-general-adaptive_searching_delay"
            beforeStaged={(v) => (v === undefined ? "3w" : v)}
            options={adaptiveSearchingDelayOption}
          ></Selector>
          <Message>
            In order to reduce search frequency, how many weeks must Bazarr wait
            after initial search.
          </Message>
          <Selector
            settingKey="settings-general-adaptive_searching_delta"
            beforeStaged={(v) => (v === undefined ? "1w" : v)}
            options={adaptiveSearchingDeltaOption}
          ></Selector>
          <Message>
            How often should Bazarr search for subtitles when in adaptive search
            mode.
          </Message>
        </CollapseBox>
        <Check
          label="Search Enabled Providers Simultaneously"
          settingKey="settings-general-multithreading"
        ></Check>
        <Message>
          Search multiple providers at once (Don't choose this on low powered
          devices)
        </Message>
        <Check
          label="Use Embedded Subtitles"
          settingKey="settings-general-use_embedded_subs"
        ></Check>
        <Message>
          Use embedded subtitles in media files when determining missing ones.
        </Message>
        <CollapseBox settingKey="settings-general-use_embedded_subs">
          <Check
            label="Ignore Embedded PGS Subtitles"
            settingKey="settings-general-ignore_pgs_subs"
          ></Check>
          <Message>
            Ignores PGS Subtitles in Embedded Subtitles detection.
          </Message>
          <Check
            label="Ignore Embedded VobSub Subtitles"
            settingKey="settings-general-ignore_vobsub_subs"
          ></Check>
          <Message>
            Ignores VobSub Subtitles in Embedded Subtitles detection.
          </Message>
          <Check
            label="Ignore Embedded ASS Subtitles"
            settingKey="settings-general-ignore_ass_subs"
          ></Check>
          <Message>
            Ignores ASS Subtitles in Embedded Subtitles detection.
          </Message>
          <Check
            label="Show Only Desired Languages"
            settingKey="settings-general-embedded_subs_show_desired"
          ></Check>
          <Message>
            Hide embedded subtitles for languages that are not currently
            desired.
          </Message>
        </CollapseBox>
      </Section>
      <Section header="Post-Processing">
        <Check
          label="Encode Subtitles To UTF8"
          settingKey="settings-general-utf8_encode"
        ></Check>
        <Message>
          Re-encode downloaded Subtitles to UTF8. Should be left enabled in most
          case.
        </Message>
        <Check
          label="Hearing Impaired"
          override={subzeroOverride("remove_HI")}
          settingKey="subzero-remove_HI"
        ></Check>
        <Message>
          Removes tags, text and characters from subtitles that are meant for
          hearing impaired people.
        </Message>
        <Check
          label="Remove Tags"
          override={subzeroOverride("remove_tags")}
          settingKey="subzero-remove_tags"
        ></Check>
        <Message>
          Removes all possible style tags from the subtitle, such as font, bold,
          color etc.
        </Message>
        <Check
          label="OCR Fixes"
          override={subzeroOverride("OCR_fixes")}
          settingKey="subzero-OCR_fixes"
        ></Check>
        <Message>
          Fix issues that happen when a subtitle gets converted from bitmap to
          text through OCR.
        </Message>
        <Check
          label="Common Fixes"
          override={subzeroOverride("common")}
          settingKey="subzero-common"
        ></Check>
        <Message>
          Fix common and whitespace/punctuation issues in subtitles.
        </Message>
        <Check
          label="Fix Uppercase"
          override={subzeroOverride("fix_uppercase")}
          settingKey="subzero-fix_uppercase"
        ></Check>
        <Message>
          Tries to make subtitles that are completely uppercase readable.
        </Message>
        <Selector
          label="Color"
          clearable
          options={colorOptions}
          override={subzeroColorOverride}
          settingKey="subzero-color"
        ></Selector>
        <Message>
          Adds color to your subtitles (for playback devices/software that don't
          ship their own color modes; only works for players that support color
          tags).
        </Message>
        <Check
          label="Reverse RTL"
          override={subzeroOverride("reverse_rtl")}
          settingKey="subzero-reverse_rtl"
        ></Check>
        <Message>
          Reverses the punctuation in right-to-left subtitles for problematic
          playback devices.
        </Message>
        <Check
          label="Permission (chmod)"
          settingKey="settings-general-chmod_enabled"
        ></Check>
        <CollapseBox settingKey="settings-general-chmod_enabled">
          <Text placeholder="0777" settingKey="settings-general-chmod"></Text>
          <Message>Must be 4 digit octal</Message>
        </CollapseBox>
        <Check
          label="Automatic Subtitles Synchronization"
          settingKey="settings-subsync-use_subsync"
        ></Check>
        <Message>
          Enable the automatic subtitles synchronization after downloading a
          subtitles.
        </Message>
        <CollapseBox settingKey="settings-subsync-use_subsync">
          <Check label="Debug" settingKey="settings-subsync-debug"></Check>
          <Message>
            Do not actually sync the subtitles but generate a .tar.gz file to be
            able to open an issue for ffsubsync. This file will reside alongside
            the media file.
          </Message>
          <Check
            label="Series Score Threshold"
            settingKey="settings-subsync-use_subsync_threshold"
          ></Check>
          <CollapseBox settingKey="settings-subsync-use_subsync_threshold">
            <Slider settingKey="settings-subsync-subsync_threshold"></Slider>
          </CollapseBox>
          <Check
            label="Movies Score Threshold"
            settingKey="settings-subsync-use_subsync_movie_threshold"
          ></Check>
          <CollapseBox settingKey="settings-subsync-use_subsync_movie_threshold">
            <Slider settingKey="settings-subsync-subsync_movie_threshold"></Slider>
          </CollapseBox>
        </CollapseBox>
        <Check
          settingKey="settings-general-use_postprocessing"
          label="Custom Post-Processing"
        ></Check>
        <Message>
          Enable the post-processing execution after downloading a subtitles.
        </Message>
        <CollapseBox settingKey="settings-general-use_postprocessing">
          <Check
            settingKey="settings-general-use_postprocessing_threshold"
            label="Series Score Threshold"
          ></Check>
          <CollapseBox settingKey="settings-general-use_postprocessing">
            <Slider settingKey="settings-general-postprocessing_threshold"></Slider>
          </CollapseBox>
          <Check
            settingKey="settings-general-use_postprocessing_threshold_movie"
            label="Movies Score Threshold"
          ></Check>
          <CollapseBox settingKey="settings-general-use_postprocessing_threshold_movie">
            <Slider settingKey="settings-general-postprocessing_threshold_movie"></Slider>
          </CollapseBox>
          <Text
            label="Command"
            settingKey="settings-general-postprocessing_cmd"
          ></Text>
          <Message>Variables you can use in your command</Message>
          <Message>
            <b>{"{{directory}}"}</b> Full path of the episode file parent
            directory
          </Message>
          <Message>
            <b>{"{{episode}}"}</b> Full path of the episode file
          </Message>
          <Message>
            <b>{"{{episode_name}}"}</b> Filename of the episode without parent
            directory or extension
          </Message>
          <Message>
            <b>{"{{subtitles}}"}</b> Full path of the subtitles file
          </Message>
          <Message>
            <b>{"{{subtitles_language}}"}</b> Language of the subtitles file
            (may include HI or forced)
          </Message>
          <Message>
            <b>{"{{subtitles_language_code2}}"}</b> 2-letter ISO-639 language
            code of the subtitles language (may include :hi or :forced)
          </Message>
          <Message>
            <b>{"{{subtitles_language_code2_dot}}"}</b> 2-letter ISO-639
            language code of the subtitles language (same as previous but with
            dot separator instead of colon)
          </Message>
          <Message>
            <b>{"{{subtitles_language_code3}}"}</b> 3-letter ISO-639 language
            code of the subtitles language (may include :hi or :forced)
          </Message>
          <Message>
            <b>{"{{subtitles_language_code3_dot}}"}</b> 3-letter ISO-639
            language code of the subtitles language (same as previous but with
            dot separator instead of colon)
          </Message>
          <Message>
            <b>{"{{episode_language}}"}</b> Audio language of the episode file
          </Message>
          <Message>
            <b>{"{{episode_language_code2}}"}</b> 2-letter ISO-639 language code
            of the episode audio language
          </Message>
          <Message>
            <b>{"{{episode_language_code3}}"}</b> 3-letter ISO-639 language code
            of the episode audio language
          </Message>
          <Message>
            <b>{"{{score}}"}</b> Score of the subtitle file
          </Message>
          <Message>
            <b>{"{{subtitle_id}}"}</b> Provider ID of the subtitle file
          </Message>
          <Message>
            <b>{"{{series_id}}"}</b> Sonarr series ID (Empty if movie)
          </Message>
          <Message>
            <b>{"{{episode_id}}"}</b> Sonarr episode ID or Radarr movie ID
          </Message>
        </CollapseBox>
      </Section>
    </Layout>
  );
};

export default SettingsSubtitlesView;
