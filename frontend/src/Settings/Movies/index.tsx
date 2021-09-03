import React, { FunctionComponent } from "react";
import {
  Check,
  Chips,
  CollapseBox,
  Group,
  Input,
  Message,
  SettingsProvider,
  Slider,
} from "../components";
import { moviesEnabledKey } from "../keys";

interface Props {}

const SettingsMoviesView: FunctionComponent<Props> = () => {
  return (
    <SettingsProvider title="Movies - Bazarr (Settings)">
      <CollapseBox>
        <CollapseBox.Control>
          <Group header="Use Movies">
            <Input>
              <Check label="Enabled" settingKey={moviesEnabledKey}></Check>
            </Input>
          </Group>
        </CollapseBox.Control>
        <CollapseBox.Content indent={false}>
          <Group header="Options">
            <Input name="Minimum Score">
              <Slider settingKey="settings-general-minimum_score_movie"></Slider>
            </Input>
            <Input name="Excluded Tags">
              <Chips settingKey="settings-movies-excluded_tags"></Chips>
              <Message>
                Movies with those tags (case sensitive) will be excluded from
                automatic download of subtitles.
              </Message>
            </Input>
            <Input>
              <Check
                label="Download Only Monitored"
                settingKey="settings-movies-only_monitored"
              ></Check>
              <Message>
                Automatic download of subtitles will only happen for monitored
                movies.
              </Message>
            </Input>
          </Group>
        </CollapseBox.Content>
      </CollapseBox>
    </SettingsProvider>
  );
};

export default SettingsMoviesView;
