import { FunctionComponent } from "react";
import { useLanguages } from "@/apis/hooks";
import {
  Check,
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
} from "@/pages/Settings/keys";
import { useEnabledLanguages } from "@/utilities/languages";
import { LanguageSelector } from "./components";

const SettingsLanguagesGeneralView: FunctionComponent = () => {
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
    </Layout>
  );
};

export default SettingsLanguagesGeneralView;
