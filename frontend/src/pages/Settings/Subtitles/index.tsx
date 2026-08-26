import { FunctionComponent } from "react";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Section,
  Selector,
  Slider,
  Text,
} from "@/pages/Settings/components";
import {
  adaptiveSearchingDelayOption,
  adaptiveSearchingDeltaOption,
  embeddedSubtitlesParserOption,
  folderOptions,
  hiExtensionOptions,
} from "./options";

const SettingsSubtitlesView: FunctionComponent = () => {
  return (
    <Layout name="Subtitles">
      <Section header="Subtitle File Options">
        <Selector
          label="Subtitle Folder"
          options={folderOptions}
          settingKey="settings-general-subfolder"
        ></Selector>
        <Message>
          Choose the folder you wish to store/read the subtitles.
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
        <Selector
          label="Hearing-impaired subtitles extension"
          options={hiExtensionOptions}
          settingKey="settings-general-hi_extension"
          allowDeselect={false}
        ></Selector>
        <Message>
          What file extension to use when saving hearing-impaired subtitles to
          disk (e.g., video.en.sdh.srt).
        </Message>
        <Check
          label="Encode Subtitles To UTF-8"
          settingKey="settings-general-utf8_encode"
        ></Check>
        <Message>
          Re-encode downloaded subtitles to UTF-8. Should be left enabled in
          most cases.
        </Message>
        <Check
          label="Change Subtitle File Permission After Download (chmod)"
          settingKey="settings-general-chmod_enabled"
        ></Check>
        <CollapseBox indent settingKey="settings-general-chmod_enabled">
          <Text placeholder="0777" settingKey="settings-general-chmod"></Text>
          <Message>
            Must be a 4 digit octal number. Only for non-Windows systems.
          </Message>
        </CollapseBox>
      </Section>
      <Section header="Embedded Subtitles Handling">
        <Check
          label="Enable .strm Support"
          settingKey="settings-general-enable_strm_support"
        ></Check>
        <Message>
          Enable support for .strm files. Bazarr will read the stream URL from
          the file and analyze it for embedded tracks.
        </Message>
        <Check
          label="Treat Embedded Subtitles as Downloaded"
          settingKey="settings-general-use_embedded_subs"
        ></Check>
        <Message>
          Treat embedded subtitles in media files as already downloaded when
          determining missing ones.
        </Message>
        <CollapseBox indent settingKey="settings-general-use_embedded_subs">
          <Selector
            settingKey="settings-general-embedded_subtitles_parser"
            settingOptions={{
              onSaved: (v) => (v === undefined ? "ffprobe" : v),
            }}
            options={embeddedSubtitlesParserOption}
          ></Selector>
          <Message>Embedded Subtitles video parser.</Message>
          <Check
            label="Ignore Embedded PGS Subtitles"
            settingKey="settings-general-ignore_pgs_subs"
          ></Check>
          <Message>
            Ignore PGS Subtitles when detecting embedded subtitles.
          </Message>
          <Check
            label="Ignore Embedded VobSub Subtitles"
            settingKey="settings-general-ignore_vobsub_subs"
          ></Check>
          <Message>
            Ignore VobSub Subtitles when detecting embedded subtitles.
          </Message>
          <Check
            label="Ignore Embedded ASS Subtitles"
            settingKey="settings-general-ignore_ass_subs"
          ></Check>
          <Message>
            Ignore ASS Subtitles when detecting embedded subtitles.
          </Message>
          <Check
            label="Show Only Desired Languages"
            settingKey="settings-general-embedded_subs_show_desired"
          ></Check>
          <Message>
            Hide Embedded Subtitles for languages that are not currently
            desired.
          </Message>
        </CollapseBox>
      </Section>
      <Section header="Upgrading Subtitles">
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
            Number of days to go back in history to upgrade subtitles.
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
      </Section>
      <Section header="Search Scores">
        <Slider
          label="Minimum Score For Episodes"
          settingKey="settings-general-minimum_score"
        ></Slider>
        <Slider
          label="Minimum Score For Movies"
          settingKey="settings-general-minimum_score_movie"
        ></Slider>
        <Message>
          Subtitles with a score below the minimum will not be downloaded
          automatically.
        </Message>
      </Section>
      <Section header="Performance / Optimization">
        <Check
          label="Adaptive Searching"
          settingKey="settings-general-adaptive_searching"
        ></Check>
        <Message>
          When enabled, Bazarr will skip searching providers for subtitles which
          have been searched recently.
        </Message>
        <CollapseBox settingKey="settings-general-adaptive_searching">
          <Selector
            settingKey="settings-general-adaptive_searching_delay"
            settingOptions={{ onSaved: (v) => (v === undefined ? "3w" : v) }}
            options={adaptiveSearchingDelayOption}
          ></Selector>
          <Message>
            The delay from the first search to adaptive searching taking effect.
            During this time window Bazarr will continue to search for
            subtitles, even if they have been searched for recently.
          </Message>
          <Selector
            settingKey="settings-general-adaptive_searching_delta"
            settingOptions={{ onSaved: (v) => (v === undefined ? "1w" : v) }}
            options={adaptiveSearchingDeltaOption}
          ></Selector>
          <Message>
            The delay between Bazarr searching for subtitles in adaptive search
            mode. If the media has been searched for more recently than this
            value, Bazarr will skip searching for subtitles.
          </Message>
        </CollapseBox>
        <Check
          label="Search Enabled Providers Simultaneously"
          settingKey="settings-general-multithreading"
        ></Check>
        <Message>
          Search multiple providers at once. (Don't choose this on low powered
          devices).
        </Message>
        <Check
          label="Skip video file hash calculation"
          settingKey="settings-general-skip_hashing"
        ></Check>
        <Message>
          Skip video file hashing during search process to prevent a sleeping
          hard disk drive from waking up. However, this may decrease your search
          results scores.
        </Message>
      </Section>
    </Layout>
  );
};

export default SettingsSubtitlesView;
