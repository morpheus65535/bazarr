import React, { FunctionComponent, useMemo } from "react";

import {
  Group,
  Selector,
  Input,
  CollapseBox,
  SettingsProvider,
} from "../components";
import { Container } from "react-bootstrap";

import {
  seriesSyncOptions,
  episodesSyncOptions,
  moviesSyncOptions,
  diskUpdateOptions,
  dayOptions,
  upgradeOptions,
} from "./options";

const SettingsSchedularView: FunctionComponent = () => {
  const timeOptions = useMemo(() => {
    let object: LooseObject = {};
    Array(24)
      .fill(undefined)
      .map((_, idx) => (object[idx.toString()] = `${idx}:00`));
    return object;
  }, []);

  return (
    <SettingsProvider title="Schedular - Bazarr (Settings)">
      <Container>
        <Group header="Sonarr/Radarr Sync">
          <Input name="Update Series List from Sonarr">
            <Selector
              options={seriesSyncOptions}
              settingKey="settings-sonarr-series_sync"
            ></Selector>
          </Input>
          <Input name="Update Episodes List from Sonarr">
            <Selector
              options={episodesSyncOptions}
              settingKey="settings-sonarr-episodes_sync"
            ></Selector>
          </Input>
          <Input name="Update Movies List from Radarr">
            <Selector
              options={moviesSyncOptions}
              settingKey="settings-radarr-movies_sync"
            ></Selector>
          </Input>
        </Group>
        <Group header="Disk Indexing">
          <CollapseBox>
            <CollapseBox.Control>
              <Input name="Update all Episode Subtitles from Disk">
                <Selector
                  settingKey="settings-sonarr-full_update"
                  options={diskUpdateOptions}
                ></Selector>
              </Input>
            </CollapseBox.Control>
            <CollapseBox.Content on={(k) => k === "Weekly"}>
              <Input name="Day of The Week">
                <Selector
                  settingKey="settings-sonarr-full_update_day"
                  options={dayOptions}
                ></Selector>
              </Input>
            </CollapseBox.Content>
            <CollapseBox.Content on={(k) => k === "Daily" || k === "Weekly"}>
              <Input name="Time of The Day">
                <Selector
                  settingKey="settings-sonarr-full_update_hour"
                  options={timeOptions}
                ></Selector>
              </Input>
            </CollapseBox.Content>
          </CollapseBox>
          <CollapseBox>
            <CollapseBox.Control>
              <Input name="Update all Movie Subtitles from Disk">
                <Selector
                  settingKey="settings-radarr-full_update"
                  options={diskUpdateOptions}
                ></Selector>
              </Input>
            </CollapseBox.Control>
            <CollapseBox.Content on={(k) => k === "Weekly"}>
              <Input name="Day of The Week">
                <Selector
                  settingKey="settings-radarr-full_update_day"
                  options={dayOptions}
                ></Selector>
              </Input>
            </CollapseBox.Content>
            <CollapseBox.Content on={(k) => k === "Daily" || k === "Weekly"}>
              <Input name="Time of The Day">
                <Selector
                  settingKey="settings-radarr-full_update_hour"
                  options={timeOptions}
                ></Selector>
              </Input>
            </CollapseBox.Content>
          </CollapseBox>
        </Group>
        <Group header="Search and Upgrade Subtitles">
          <Input name="Search for Missing Series Subtitles">
            <Selector
              settingKey="settings-general-wanted_search_frequency"
              options={upgradeOptions}
            ></Selector>
          </Input>
          <Input name="Search for Missing Movies Subtitles">
            <Selector
              options={upgradeOptions}
              settingKey="settings-general-wanted_search_frequency_movie"
            ></Selector>
          </Input>
          <Input name="Upgrade Previously Downloaded Subtitles">
            <Selector
              options={upgradeOptions}
              settingKey="settings-general-upgrade_frequency"
            ></Selector>
          </Input>
        </Group>
      </Container>
    </SettingsProvider>
  );
};

export default SettingsSchedularView;
