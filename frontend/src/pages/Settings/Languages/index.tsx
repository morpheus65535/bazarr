import { useLanguageProfiles, useLanguages } from "@/apis/hooks";
import { useEnabledLanguages } from "@/utilities/languages";
import { isArray } from "lodash";
import { FunctionComponent } from "react";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Section,
  useLatest,
} from "../components";
import { enabledLanguageKey, languageProfileKey } from "../keys";
import { LanguageSelector, ProfileSelector } from "./components";
import Table from "./table";

export function useLatestEnabledLanguages() {
  const { data } = useEnabledLanguages();
  const latest = useLatest<Language.Info[]>(enabledLanguageKey, isArray);

  if (latest) {
    return latest;
  } else {
    return data;
  }
}

export function useLatestProfiles() {
  const { data = [] } = useLanguageProfiles();
  const latest = useLatest<Language.Profile[]>(languageProfileKey, isArray);

  if (latest) {
    return latest;
  } else {
    return data;
  }
}

const SettingsLanguagesView: FunctionComponent = () => {
  const { data: languages } = useLanguages();
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
          settingKey={enabledLanguageKey}
          options={languages ?? []}
        ></LanguageSelector>
      </Section>
      <Section header="Languages Profiles">
        <Table></Table>
      </Section>
      <Section header="Default Settings">
        <CollapseBox>
          <CollapseBox.Control>
            <Check
              label="Series"
              settingKey="settings-general-serie_default_enabled"
            ></Check>
            <Message>
              Apply only to Series added to Bazarr after enabling this option.
            </Message>
          </CollapseBox.Control>
          <CollapseBox.Content indent>
            <ProfileSelector
              label="Profile"
              settingKey="settings-general-serie_default_profile"
            ></ProfileSelector>
          </CollapseBox.Content>
        </CollapseBox>
        <CollapseBox>
          <CollapseBox.Control>
            <Check
              label="Movies"
              settingKey="settings-general-movie_default_enabled"
            ></Check>
            <Message>
              Apply only to Movies added to Bazarr after enabling this option.
            </Message>
          </CollapseBox.Control>
          <CollapseBox.Content>
            <ProfileSelector
              label="Profile"
              settingKey="settings-general-movie_default_profile"
            ></ProfileSelector>
          </CollapseBox.Content>
        </CollapseBox>
      </Section>
    </Layout>
  );
};

export default SettingsLanguagesView;
