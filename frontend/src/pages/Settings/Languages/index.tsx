import { useLanguageProfiles, useLanguages } from "@/apis/hooks";
import { useEnabledLanguages } from "@/utilities/languages";
import { FunctionComponent } from "react";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Section,
  Selector,
} from "../components";
import {
  defaultUndAudioLang,
  defaultUndEmbeddedSubtitlesLang,
  enabledLanguageKey,
  languageProfileKey,
} from "../keys";
import { useSettingValue } from "../utilities/hooks";
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
        <Message>TODO: Description</Message>
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
          label="Treat unknown language embedded subtitles track as (changing this will trigger full subtitles indexation using cache)"
          placeholder="Select languages"
          options={undEmbeddedSubtitlesLanguages.map((v) => {
            return { label: v.name, value: v.code2 };
          })}
          settingOptions={{
            onSubmit: (v) => (v === null ? "" : v),
          }}
        ></Selector>
      </Section>
      <Section header="Languages Profiles">
        <Table></Table>
      </Section>
      <Section header="Default Settings">
        <Check
          label="Series"
          settingKey="settings-general-serie_default_enabled"
        ></Check>
        <Message>
          Apply only to Series added to Bazarr after enabling this option.
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
          Apply only to Movies added to Bazarr after enabling this option.
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
