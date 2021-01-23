import React, { FunctionComponent, useState, useMemo } from "react";
import { Container } from "react-bootstrap";
import { connect } from "react-redux";

import { LanguageSelector } from "../../Components";

import Table from "./table";

import {
  Group,
  Message,
  Input,
  Check,
  Selector,
  CollapseBox,
} from "../Components";

import SettingTemplate from "../Components/template";

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
  const [enabled, setEnabled] = useState(props.enabled);
  const [profiles, setProfiles] = useState(props.profiles);

  const profileOptions = useMemo<Pair[]>(
    () =>
      profiles.map<Pair>((v) => {
        return { key: v.profileId.toString(), value: v.name };
      }),
    [profiles]
  );

  return (
    <SettingTemplate title="Languages - Bazarr (Settings)">
      {(settings, update) => (
        <Container>
          <Group header="Subtitles Language">
            <Input>
              <Check
                label="Single Language"
                defaultValue={settings.general.single_language}
                onChange={(v) => update(v, "settings-general-single_language")}
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
                multiple
                defaultSelect={enabled}
                options={props.languages}
                onChange={(val: Language[]) => {
                  setEnabled(val);
                  const langs = val.map((v) => v.code2);
                  update(langs, "languages-enabled");
                }}
              ></LanguageSelector>
            </Input>
          </Group>
          <Group header="Languages Profiles">
            <Table
              languages={enabled}
              profiles={profiles}
              setProfiles={(profiles: LanguagesProfile[]) => {
                setProfiles(profiles);

                update(JSON.stringify(profiles), "languages-profiles");
              }}
            ></Table>
          </Group>
          <Group header="Default Settings">
            <CollapseBox
              indent
              defaultOpen={settings.general.serie_default_enabled}
              control={(change) => (
                <Input>
                  <Check
                    label="Series"
                    defaultValue={settings.general.serie_default_enabled}
                    onChange={(v) => {
                      change(v);
                      update(v, "settings-general-serie_default_enabled");
                    }}
                  ></Check>
                  <Message type="info">
                    Apply only to Series added to Bazarr after enabling this
                    option.
                  </Message>
                </Input>
              )}
            >
              <Input name="Profile">
                <Selector
                  options={profileOptions}
                  nullKey="None"
                  defaultKey={settings.general.serie_default_profile?.toString()}
                  onSelect={(v) => {
                    update(
                      v === "None" ? "" : v,
                      "settings-general-serie_default_profile"
                    );
                  }}
                ></Selector>
              </Input>
            </CollapseBox>
            <CollapseBox
              indent
              defaultOpen={settings.general.movie_default_enabled}
              control={(change) => (
                <Input>
                  <Check
                    label="Movies"
                    defaultValue={settings.general.movie_default_enabled}
                    onChange={(v) => {
                      change(v);
                      update(v, "settings-general-movie_default_enabled");
                    }}
                  ></Check>
                  <Message type="info">
                    Apply only to Movies added to Bazarr after enabling this
                    option.
                  </Message>
                </Input>
              )}
            >
              <Input name="Profile">
                <Selector
                  options={profileOptions}
                  nullKey="None"
                  defaultKey={settings.general.movie_default_profile?.toString()}
                  onSelect={(v) => {
                    update(
                      v === "None" ? "" : v,
                      "settings-general-movie_default_profile"
                    );
                  }}
                ></Selector>
              </Input>
            </CollapseBox>
          </Group>
        </Container>
      )}
    </SettingTemplate>
  );
};

export default connect(mapStateToProps, {})(SettingsLanguagesView);
