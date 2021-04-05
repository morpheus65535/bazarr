import React, { FunctionComponent, useMemo } from "react";
import {
  CollapseBox,
  Group,
  Input,
  Selector,
  SettingsProvider,
} from "../components";
import {
  dayOptions,
  diskUpdateOptions,
  moviesSyncOptions,
  seriesSyncOptions,
  upgradeOptions,
} from "./options";

const SettingsSchedulerView: FunctionComponent = () => {
  const timeOptions = useMemo(() => {
    return Array(24)
      .fill(null)
      .map<SelectorOption<number>>((_, idx) => ({
        label: `${idx}:00`,
        value: idx,
      }));
  }, []);

  return (
    <SettingsProvider title="Scheduler - Bazarr (Settings)">
      <Group header="Sonarr/Radarr Sync">
        <Input name="Sync with Sonarr">
          <Selector
            options={seriesSyncOptions}
            settingKey="settings-sonarr-series_sync"
          ></Selector>
        </Input>
        <Input name="Sync with Radarr">
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
    </SettingsProvider>
  );
};

export default SettingsSchedulerView;
