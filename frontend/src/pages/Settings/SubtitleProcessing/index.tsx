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
  colorOptions,
  forceAudioOption,
  providerOptions,
  syncMaxOffsetSecondsOptions,
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

const SettingsSubtitleProcessingView: FunctionComponent = () => {
  return (
    <Layout name="Subtitle Processing">
      <Section
        header="Whisper As Fallback"
        collapsible
        defaultCollapsed
        summary="AI transcription fallback for low-scoring results"
      >
        <Check
          label="Use Whisper as Fallback for Automated Searches"
          settingKey="settings-general-use_whisper_fallback"
        ></Check>
        <CollapseBox settingKey={"settings-general-use_whisper_fallback"}>
          <Message>
            When enabled, Bazarr will ignore the Radarr/Sonarr minimum score and
            fall back to a Whisper generated subtitle when no provider reaches
            that minimum score. To avoid overloading Whisper, this fallback is
            used only during automated tasks like Search for Missing Movie
            Subtitles and Search for Missing Series Subtitles, or by invoking
            Search from the Wanted menu. You are responsible for ensuring that
            only one Whisper transcription or translation runs at a time, unless
            your hardware can handle more.
          </Message>
        </CollapseBox>
        <CollapseBox settingKey={"settings-general-use_whisper_fallback"}>
          <Check
            label="Use Whisper as Fallback for Single Series Searches"
            settingKey="settings-general-use_whisper_fallback_series"
          ></Check>
          <CollapseBox
            settingKey={"settings-general-use_whisper_fallback_series"}
          >
            <Message>
              When enabled, Bazarr will also use Whisper fallback for single
              series subtitle searches. All of the warnings about overloading
              Whisper from the previous setting also apply to this one.
            </Message>
          </CollapseBox>
        </CollapseBox>
      </Section>

      <Section
        header="Sub-Zero Subtitle Content Modifications"
        collapsible
        defaultCollapsed
        summary="Optional subtitle content fixes"
      >
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

      <Section
        header="Audio Synchronization"
        collapsible
        defaultCollapsed
        summary="Automatic subtitle timing alignment"
      >
        <Check
          label="Enable Automatic Subtitles Audio Synchronization"
          settingKey="settings-subsync-use_subsync"
        ></Check>
        <Message>
          Enable automatic audio synchronization after downloading subtitles for
          series and movies based on selections below.
        </Message>
        <CollapseBox settingKey="settings-subsync-use_subsync">
          <Message>
            This feature uses ffsubsync, which can provide better
            synchronization results than traditional methods, especially for
            subtitles that are significantly out of sync. However, it may also
            increase the time it takes to process subtitles. If you have a lot
            of subtitles that need synchronization or if you are on a
            low-powered device, you may want to leave this option disabled and
            synchronize subtitles manually when needed.
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
          <MultiSelector
            placeholder="Select providers..."
            label="Providers to Exclude from Automatic Synchronization"
            clearable
            options={providerOptions}
            settingKey="settings-subsync-checker-blacklisted_providers"
          ></MultiSelector>
          <Message>
            Subtitles downloaded from the providers listed above will not be
            automatically synchronized.
          </Message>
          <Section header="Advanced FFsubsync Options">
            <Selector
              label="Synchronization Reference"
              options={forceAudioOption}
              settingKey="settings-subsync-force_audio"
            ></Selector>
            <Message>
              Choose whether to use the audio track or the embedded subtitle as
              the reference for synchronization. Using the audio track can
              provide better results, especially when the embedded subtitles are
              not properly synced or have a different framerate than the video.
              However, it may also increase the synchronization time, as
              analyzing the audio track is more resource-intensive than
              analyzing the embedded subtitles.
            </Message>
            <CollapseBox
              indent
              settingKey="settings-subsync-force_audio"
              on={(v) => v === true || v === "true"}
            >
              <Check
                label="Prefer Original Language Audio Track"
                settingKey="settings-subsync-use_original_language"
              ></Check>
              <Message>
                When enabled, subsync overrides the default audio track with the
                one matching the show or movie's original language (from
                Sonarr/Radarr metadata). Falls back to the default audio track
                if the original language is not present in the file (e.g.
                dubbed-only release).
              </Message>
            </CollapseBox>
            <CollapseBox
              indent
              settingKey="settings-subsync-force_audio"
              on={(v) => v === false || v === "false"}
            >
              <Check
                label="Prefer Original Language Audio Track"
                settingKey="settings-subsync-auto_use_original_language"
              ></Check>
              <Message>
                When enabled, automatic synchronization aligns to the audio
                track matching the show or movie's original language (from
                Sonarr/Radarr metadata) instead of using the embedded subtitle
                as reference. Falls back to ffsubsync's default reference if the
                original language is not present in the file.
              </Message>
            </CollapseBox>
            <Check
              label="Do Not Fix Framerate Mismatch"
              settingKey="settings-subsync-no_fix_framerate"
            ></Check>
            <Message>
              If specified, subsync will not attempt to correct a framerate
              mismatch between reference and subtitles.
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
              label="Generate Debug File Instead of Synchronizing"
              settingKey="settings-subsync-debug"
            ></Check>
            <Message>
              Do not actually synchronize the subtitles but generate a .tar.gz
              file to be able to open an issue for ffsubsync. This file will
              reside alongside the media file.
            </Message>
          </Section>
        </CollapseBox>
      </Section>

      <Section
        header="Custom Post-Processing"
        collapsible
        defaultCollapsed
        summary="Run a command after downloading"
      >
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
    </Layout>
  );
};

export default SettingsSubtitleProcessingView;
