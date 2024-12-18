import { FunctionComponent } from "react";
import { Text as MantineText } from "@mantine/core";
import { useLanguageProfiles, useLanguages } from "@/apis/hooks";
import {
  Check,
  Chips,
  CollapseBox,
  Layout,
  Message,
  Section,
  Selector,
} from "@/pages/Settings/components";
import {
  defaultUndAudioLang,
  defaultUndEmbeddedSubtitlesLang,
  enabledLanguageKey,
  languageProfileKey,
} from "@/pages/Settings/keys";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";
import { useEnabledLanguages } from "@/utilities/languages";
import { LanguageSelector, ProfileSelector } from "./components";
import EqualsTable from "./equals";
import Table from "./table";

export function useLatestEnabledLanguages() {
  const { data } = useEnabledLanguages();
  const latest = useSettingValue<Language.Info[]>(enabledLanguageKey);

  if (latest) {
    return latest;
  } else {
    return data;
  }
}

export function useLatestProfiles() {
  const { data = [] } = useLanguageProfiles();
  const latest = useSettingValue<Language.Profile[]>(languageProfileKey);

  if (latest) {
    return latest;
  } else {
    return data;
  }
}

const SettingsLanguagesView: FunctionComponent = () => {
  const { data: languages } = useLanguages();
  const { data: undAudioLanguages } = useEnabledLanguages();
  const { data: undEmbeddedSubtitlesLanguages } = useEnabledLanguages();
  return (
    <Layout name="Languages">
      <Section header="Subtitles Language">
        <Check
          label="Single Language"
          settingKey="settings-general-single_language"
        ></Check>
        <Message>
          Download a single Subtitles file without adding the language code to
          the filename.
        </Message>
        <Message type="warning">
          We don't recommend enabling this option unless absolutely required
          (ie: media player not supporting language code in subtitles filename).
          Results may vary.
        </Message>
        <LanguageSelector
          label="Languages Filter"
          placeholder="Select languages"
          settingKey={enabledLanguageKey}
          options={languages ?? []}
        ></LanguageSelector>
      </Section>

      <Section header="Language Equals">
        <Message>
          Treat the following languages as equal across all providers.
        </Message>
        <EqualsTable></EqualsTable>
      </Section>

      <Section header="Embedded Tracks Language">
        <Check
          label="Deep analyze media file to get audio tracks language."
          settingKey="settings-general-parse_embedded_audio_track"
        ></Check>
        <CollapseBox
          indent
          settingKey="settings-general-parse_embedded_audio_track"
        >
          <Selector
            clearable
            settingKey={defaultUndAudioLang}
            label="Treat unknown language audio track as (changing this will trigger missing subtitles calculation)"
            placeholder="Select languages"
            options={undAudioLanguages.map((v) => {
              return { label: v.name, value: v.code2 };
            })}
            settingOptions={{
              onSubmit: (v) => (v === null ? "" : v),
            }}
          ></Selector>
        </CollapseBox>
        <Selector
          clearable
          settingKey={defaultUndEmbeddedSubtitlesLang}
          label="Treat unknown language embedded subtitles track as (changing this will trigger full subtitles indexing using cache)"
          placeholder="Select languages"
          options={undEmbeddedSubtitlesLanguages.map((v) => {
            return { label: v.name, value: v.code2 };
          })}
          settingOptions={{
            onSubmit: (v) => (v === null ? "" : v),
          }}
        ></Selector>
      </Section>
      <Section header="Languages Profile">
        <Table></Table>
      </Section>
      <Section header="Tag-Based Automatic Language Profile Selection Settings">
        <Message>
          If enabled, Bazarr will look at the names of all tags of a Series from
          Sonarr (or a Movie from Radarr) to find a matching Bazarr language
          profile tag. It will use as the language profile the FIRST tag from
          Sonarr/Radarr that matches the tag of a Bazarr language profile
          EXACTLY. If multiple tags match, there is no guarantee as to which one
          will be used, so choose your tag names carefully. Also, if you update
          the tag names in Sonarr/Radarr, Bazarr will detect this and repeat the
          matching process for the affected shows. However, if a show's only
          matching tag is removed from Sonarr/Radarr, Bazarr will NOT remove the
          show's existing language profile for that reason. But if you wish to
          have language profiles removed automatically by tag value, simply
          enter a list of one or more tags in the{" "}
          <MantineText fw={700} span>
            Remove Profile Tags
          </MantineText>{" "}
          entry list below. If your video tag matches one of the tags in that
          list, then Bazarr will remove the language profile for that video. If
          there is a conflict between profile selection and profile removal,
          then profile removal wins out and is performed.
        </Message>
        <Check
          label="Series"
          settingKey="settings-general-serie_tag_enabled"
        ></Check>
        <Check
          label="Movies"
          settingKey="settings-general-movie_tag_enabled"
        ></Check>
        <Chips
          label="Remove Profile Tags"
          settingKey="settings-general-remove_profile_tags"
          sanitizeFn={(values: string[] | null) =>
            values?.map((item) =>
              item.replace(/[^a-z0-9_-]/gi, "").toLowerCase(),
            )
          }
        ></Chips>
        <Message>
          Enter tag values that will trigger a language profile removal. Leave
          empty if you don't want Bazarr to remove language profiles.
        </Message>
      </Section>
      <Section header="Default Language Profiles For Newly Added Shows">
        <Check
          label="Series"
          settingKey="settings-general-serie_default_enabled"
        ></Check>
        <Message>
          Will apply only to Series added to Bazarr after enabling this option.
        </Message>

        <CollapseBox indent settingKey="settings-general-serie_default_enabled">
          <ProfileSelector
            label="Profile"
            placeholder="Select a profile"
            settingKey="settings-general-serie_default_profile"
          ></ProfileSelector>
        </CollapseBox>

        <Check
          label="Movies"
          settingKey="settings-general-movie_default_enabled"
        ></Check>
        <Message>
          Will apply only to Movies added to Bazarr after enabling this option.
        </Message>

        <CollapseBox indent settingKey="settings-general-movie_default_enabled">
          <ProfileSelector
            label="Profile"
            placeholder="Select a profile"
            settingKey="settings-general-movie_default_profile"
          ></ProfileSelector>
        </CollapseBox>
      </Section>
    </Layout>
  );
};

export default SettingsLanguagesView;
