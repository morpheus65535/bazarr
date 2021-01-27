import React, { FunctionComponent, useContext } from "react";
import { connect } from "react-redux";
import { isArray } from "lodash";
import Table from "./table";
import {
  Group,
  Message,
  Input,
  Check,
  CollapseBox,
  SettingsProvider,
  useLatest,
} from "../components";

import { LanguageSelector, ProfileSelector } from "./components";

import { enabledLanguageKey, languageProfileKey } from "../keys";

const EnabledLanguageContext = React.createContext<Language[]>([]);
const LanguagesProfileContext = React.createContext<LanguagesProfile[]>([]);

export function useEnabledLanguages() {
  const list = useContext(EnabledLanguageContext);
  const latest = useLatest<Language[]>(enabledLanguageKey, isArray);

  if (latest) {
    return latest;
  } else {
    return list;
  }
}

export function useLanguagesProfile() {
  const list = useContext(LanguagesProfileContext);
  const latest = useLatest<LanguagesProfile[]>(languageProfileKey, isArray);

  if (latest) {
    return latest;
  } else {
    return list;
  }
}

interface Props {
  languages: Language[];
  enabled: Language[];
  profiles: LanguagesProfile[];
}

function mapStateToProps({ system }: StoreState) {
  return {
    languages: system.languages.items,
    enabled: system.enabledLanguage.items,
    profiles: system.languagesProfiles.items,
  };
}

const SettingsLanguagesView: FunctionComponent<Props> = (props) => {
  const { languages, enabled, profiles } = props;

  return (
    <SettingsProvider title="Languages - Bazarr (Settings)">
      <EnabledLanguageContext.Provider value={enabled}>
        <LanguagesProfileContext.Provider value={profiles}>
          <Group header="Subtitles Language">
            <Input>
              <Check
                label="Single Language"
                settingKey="settings-general-single_language"
              ></Check>
              <Message type="info">
                Download a single Subtitles file without adding the language
                code to the filename.
              </Message>
              <Message type="warning">
                We don't recommend enabling this option unless absolutely
                required (ie: media player not supporting language code in
                subtitles filename). Results may vary.
              </Message>
            </Input>
            <Input name="Languages Filter">
              <LanguageSelector
                settingKey={enabledLanguageKey}
                options={languages}
              ></LanguageSelector>
            </Input>
          </Group>
          <Group header="Languages Profiles">
            <Table></Table>
          </Group>
          <Group header="Default Settings">
            <CollapseBox>
              <CollapseBox.Control>
                <Input>
                  <Check
                    label="Series"
                    settingKey="settings-general-serie_default_enabled"
                  ></Check>
                  <Message type="info">
                    Apply only to Series added to Bazarr after enabling this
                    option.
                  </Message>
                </Input>
              </CollapseBox.Control>
              <CollapseBox.Content indent>
                <Input name="Profile">
                  <ProfileSelector settingKey="settings-general-serie_default_profile"></ProfileSelector>
                </Input>
              </CollapseBox.Content>
            </CollapseBox>
            <CollapseBox>
              <CollapseBox.Control>
                <Input>
                  <Check
                    label="Movies"
                    settingKey="settings-general-movie_default_enabled"
                  ></Check>
                  <Message type="info">
                    Apply only to Movies added to Bazarr after enabling this
                    option.
                  </Message>
                </Input>
              </CollapseBox.Control>
              <CollapseBox.Content>
                <Input name="Profile">
                  <ProfileSelector settingKey="settings-general-movie_default_profile"></ProfileSelector>
                </Input>
              </CollapseBox.Content>
            </CollapseBox>
          </Group>
        </LanguagesProfileContext.Provider>
      </EnabledLanguageContext.Provider>
    </SettingsProvider>
  );
};

export default connect(mapStateToProps, {})(SettingsLanguagesView);
