import React, { FunctionComponent } from "react";
import { Code, Space, Table, Text as MantineText } from "@mantine/core";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  MultiSelector,
  Section,
  Selector,
  Slider,
  Text,
} from "@/pages/Settings/components";
import {
  SubzeroColorModification,
  SubzeroModification,
} from "@/pages/Settings/utilities/modifications";
import {
  adaptiveSearchingDelayOption,
  adaptiveSearchingDeltaOption,
  colorOptions,
  embeddedSubtitlesParserOption,
  folderOptions,
  hiExtensionOptions,
  providerOptions,
  syncMaxOffsetSecondsOptions,
  translatorOption,
} from "./options";

interface CommandOption {
  option: string;
  description: string;
}

const commandOptions: CommandOption[] = [
  {
    option: "directory",
    description: "Full path of the episode file parent directory",
  },
  {
    option: "episode",
    description: "Full path of the episode file",
  },
  {
    option: "episode_name",
    description:
      "Filename of the episode without parent directory or extension",
  },
  {
    option: "subtitles",
    description: "Full path of the subtitles file",
  },
  {
    option: "subtitles_language",
    description: "Language of the subtitles file (may include HI or forced)",
  },
  {
    option: "subtitles_language_code2",
    description:
      "2-letter ISO-639 language code of the subtitles language (may include :hi or :forced)",
  },
  {
    option: "subtitles_language_code2_dot",
    description:
      "2-letter ISO-639 language code of the subtitles language (same as previous but with dot separator instead of colon)",
  },
  {
    option: "subtitles_language_code3",
    description:
      "3-letter ISO-639 language code of the subtitles language (may include :hi or :forced)",
  },
  {
    option: "subtitles_language_code3_dot",
    description:
      "3-letter ISO-639 language code of the subtitles language (same as previous but with dot separator instead of colon)",
  },
  {
    option: "episode_language",
    description: "Audio language of the episode file",
  },
  {
    option: "episode_language_code2",
    description: "2-letter ISO-639 language code of the episode audio language",
  },
  {
    option: "episode_language_code3",
    description: "3-letter ISO-639 language code of the episode audio language",
  },
  {
    option: "score",
    description: "Score of the subtitle file",
  },
  {
    option: "subtitle_id",
    description: "Provider ID of the subtitle file",
  },
  {
    option: "provider",
    description: "Provider of the subtitle file",
  },
  {
    option: "uploader",
    description: "Uploader of the subtitle file",
  },
  {
    option: "release_info",
    description: "Release info for the subtitle file",
  },
  {
    option: "series_id",
    description: "Sonarr series ID (Empty if movie)",
  },
  {
    option: "episode_id",
    description: "Sonarr episode ID or Radarr movie ID",
  },
];

const commandOptionElements: React.JSX.Element[] = commandOptions.map(
  (op, idx) => (
    <tr key={idx}>
      <td>
        <Code>{op.option}</Code>
      </td>
      <td>{op.description}</td>
    </tr>
  ),
);

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
      <Section header="Sub-Zero Subtitle Content Modifications">
        <Message>
          After downloaded, content of the subtitles will be modified based on
          options selected below.
        </Message>
        <Check
          label="Hearing Impaired"
          settingOptions={{ onLoaded: SubzeroModification("remove_HI") }}
          settingKey="subzero-remove_HI"
        ></Check>
        <Message>
          Removes tags, text and characters from subtitles that are meant for
          hearing impaired people.
        </Message>
        <Check
          label="Remove Tags"
          settingOptions={{ onLoaded: SubzeroModification("remove_tags") }}
          settingKey="subzero-remove_tags"
        ></Check>
        <Message>
          Removes all possible style tags from the subtitle, such as font, bold,
          color etc.
        </Message>
        <Check
          label="Remove Emoji"
          settingOptions={{ onLoaded: SubzeroModification("emoji") }}
          settingKey="subzero-emoji"
        ></Check>
        <Message>Removes emoji characters from subtitles.</Message>
        <Check
          label="OCR Fixes"
          settingOptions={{ onLoaded: SubzeroModification("OCR_fixes") }}
          settingKey="subzero-OCR_fixes"
        ></Check>
        <Message>
          Fix issues that happen when a subtitle gets converted from bitmap to
          text through OCR.
        </Message>
        <Check
          label="Common Fixes"
          settingOptions={{ onLoaded: SubzeroModification("common") }}
          settingKey="subzero-common"
        ></Check>
        <Message>
          Fix common and whitespace/punctuation issues in subtitles.
        </Message>
        <Check
          label="Fix Uppercase"
          settingOptions={{
            onLoaded: SubzeroModification("fix_uppercase"),
          }}
          settingKey="subzero-fix_uppercase"
        ></Check>
        <Message>
          Tries to make subtitles that are completely uppercase readable.
        </Message>
        <Selector
          placeholder="Select a color..."
          label="Color"
          clearable
          options={colorOptions}
          settingOptions={{ onLoaded: SubzeroColorModification }}
          settingKey="subzero-color"
        ></Selector>
        <Message>
          Adds color to your subtitles (for playback devices/software that don't
          ship their own color modes; only works for players that support color
          tags).
        </Message>
        <Check
          label="Reverse RTL"
          settingOptions={{ onLoaded: SubzeroModification("reverse_rtl") }}
          settingKey="subzero-reverse_rtl"
        ></Check>
        <Message>
          Reverses the punctuation in right-to-left subtitles for problematic
          playback devices.
        </Message>
      </Section>
      <Section header="Audio Synchronization / Alignment">
        <Check
          label="Always use Audio Track as Reference for Syncing"
          settingKey="settings-subsync-force_audio"
        ></Check>
        <Message>
          Use the audio track as reference for syncing, instead of the embedded
          subtitle.
        </Message>
        <Check
          label="Do Not Fix Framerate Mismatch"
          settingKey="settings-subsync-no_fix_framerate"
        ></Check>
        <Message>
          If specified, subsync will not attempt to correct a framerate mismatch
          between reference and subtitles.
        </Message>
        <Check
          label="Golden-Section Search"
          settingKey="settings-subsync-gss"
        ></Check>
        <Message>
          If specified, use golden-section search to try to find the optimal
          framerate ratio between video and subtitles.
        </Message>
        <Selector
          label="Max Offset Seconds"
          options={syncMaxOffsetSecondsOptions}
          settingKey="settings-subsync-max_offset_seconds"
          defaultValue={60}
        ></Selector>
        <Message>
          The max allowed offset seconds for any subtitle segment.
        </Message>
        <Check
          label="Automatic Subtitles Audio Synchronization"
          settingKey="settings-subsync-use_subsync"
        ></Check>
        <Message>
          Enable automatic audio synchronization after downloading subtitles.
        </Message>
        <CollapseBox indent settingKey="settings-subsync-use_subsync">
          <MultiSelector
            placeholder="Select providers..."
            label="Do not sync subtitles downloaded from those providers"
            clearable
            options={providerOptions}
            settingKey="settings-subsync-checker-blacklisted_providers"
          ></MultiSelector>
          <Check label="Debug" settingKey="settings-subsync-debug"></Check>
          <Message>
            Do not actually sync the subtitles but generate a .tar.gz file to be
            able to open an issue for ffsubsync. This file will reside alongside
            the media file.
          </Message>
          <Check
            label="Series Score Threshold For Audio Sync"
            settingKey="settings-subsync-use_subsync_threshold"
          ></Check>
          <CollapseBox
            indent
            settingKey="settings-subsync-use_subsync_threshold"
          >
            <Slider settingKey="settings-subsync-subsync_threshold"></Slider>
            <Space />
            <Message>
              Only series subtitles with scores{" "}
              <MantineText fw={700} span>
                below
              </MantineText>{" "}
              this value will be automatically synchronized.
            </Message>
          </CollapseBox>
          <Check
            label="Movies Score Threshold For Audio Sync"
            settingKey="settings-subsync-use_subsync_movie_threshold"
          ></Check>
          <CollapseBox
            indent
            settingKey="settings-subsync-use_subsync_movie_threshold"
          >
            <Slider settingKey="settings-subsync-subsync_movie_threshold"></Slider>
            <Space />
            <Message>
              Only movie subtitles with scores{" "}
              <MantineText fw={700} span>
                below
              </MantineText>{" "}
              this value will be automatically synchronized.
            </Message>
          </CollapseBox>
        </CollapseBox>
      </Section>
      <Section header="Custom Post-Processing">
        <Check
          settingKey="settings-general-use_postprocessing"
          label="Custom Post-Processing"
        ></Check>
        <Message>
          Enable automatic execution of the post-processing command specified
          below after downloading a subtitle.
        </Message>
        <CollapseBox indent settingKey="settings-general-use_postprocessing">
          <Check
            settingKey="settings-general-use_postprocessing_threshold"
            label="Series Score Threshold For Post-Processing"
          ></Check>
          <CollapseBox
            indent
            settingKey="settings-general-use_postprocessing_threshold"
          >
            <Slider settingKey="settings-general-postprocessing_threshold"></Slider>
            <Space />
            <Message>
              Only series subtitles with scores{" "}
              <MantineText fw={700} span>
                below
              </MantineText>{" "}
              this value will be automatically post-processed.
            </Message>
          </CollapseBox>
          <Check
            settingKey="settings-general-use_postprocessing_threshold_movie"
            label="Movies Score Threshold For Post-Processing"
          ></Check>
          <CollapseBox
            indent
            settingKey="settings-general-use_postprocessing_threshold_movie"
          >
            <Slider settingKey="settings-general-postprocessing_threshold_movie"></Slider>
            <Space />
            <Message>
              Only movie subtitles with scores{" "}
              <MantineText fw={700} span>
                below
              </MantineText>{" "}
              this value will be automatically post-processed.
            </Message>
          </CollapseBox>
          <Text
            label="Command"
            settingKey="settings-general-postprocessing_cmd"
          ></Text>
          <Table highlightOnHover fs="sm">
            <tbody>{commandOptionElements}</tbody>
          </Table>
        </CollapseBox>
      </Section>
      <Section header="Translating">
        <Slider
          label="Score for Translated Episode and Movie Subtitles"
          settingKey="settings-translator-default_score"
        ></Slider>
        <Selector
          label="Translator"
          clearable
          options={translatorOption}
          placeholder="Default translator"
          settingKey="settings-translator-translator_type"
        ></Selector>
        <CollapseBox
          settingKey="settings-translator-translator_type"
          on={(val) => val === "gemini"}
        >
          <Text
            label="Gemini model"
            settingKey="settings-translator-gemini_model"
          />
          <Text
            label="Gemini API key"
            settingKey="settings-translator-gemini_key"
          ></Text>
          <Message>
            You can generate it here: https://aistudio.google.com/apikey
          </Message>
        </CollapseBox>
        <CollapseBox
          settingKey="settings-translator-translator_type"
          on={(val) => val === "lingarr"}
        >
          <Text
            label="Lingarr endpoint"
            settingKey="settings-translator-lingarr_url"
          />
          <Message>Base URL of Lingarr (e.g., http://localhost:9876)</Message>
        </CollapseBox>
        <Check
          label="Add translation info at the beginning"
          settingKey="settings-translator-translator_info"
        ></Check>
      </Section>
    </Layout>
  );
};

export default SettingsSubtitlesView;
