import React, { FunctionComponent, useMemo } from "react";
import {
  Check,
  CollapseBox,
  Group,
  Input,
  Message,
  Selector,
  SettingsProvider,
} from "../components";
import { dayOptions, diskUpdateOptions, upgradeOptions } from "./options";

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
      <Group header="Disk Indexing">
        <CollapseBox>
          <CollapseBox.Control>
            <Input name="Update all Episode Subtitles from Disk">
              <Selector
                settingKey="settings-series-full_update"
                options={diskUpdateOptions}
              ></Selector>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content on={(k) => k === "Weekly"}>
            <Input name="Day of The Week">
              <Selector
                settingKey="settings-series-full_update_day"
                options={dayOptions}
              ></Selector>
            </Input>
          </CollapseBox.Content>
          <CollapseBox.Content on={(k) => k === "Daily" || k === "Weekly"}>
            <Input name="Time of The Day">
              <Selector
                settingKey="settings-series-full_update_hour"
                options={timeOptions}
              ></Selector>
            </Input>
          </CollapseBox.Content>
          <Input>
            <Check
              label="Use cached ffprobe results"
              settingKey="settings-series-use_ffprobe_cache"
            ></Check>
            <Message>
              If disabled, Bazarr will use ffprobe to index video file
              properties on each run. This will result in higher disk I/O.
            </Message>
          </Input>
        </CollapseBox>
        <CollapseBox>
          <CollapseBox.Control>
            <Input name="Update all Movie Subtitles from Disk">
              <Selector
                settingKey="settings-movies-full_update"
                options={diskUpdateOptions}
              ></Selector>
            </Input>
          </CollapseBox.Control>
          <CollapseBox.Content on={(k) => k === "Weekly"}>
            <Input name="Day of The Week">
              <Selector
                settingKey="settings-movies-full_update_day"
                options={dayOptions}
              ></Selector>
            </Input>
          </CollapseBox.Content>
          <CollapseBox.Content on={(k) => k === "Daily" || k === "Weekly"}>
            <Input name="Time of The Day">
              <Selector
                settingKey="settings-movies-full_update_hour"
                options={timeOptions}
              ></Selector>
            </Input>
          </CollapseBox.Content>
          <Input>
            <Check
              label="Use cached ffprobe results"
              settingKey="settings-movies-use_ffprobe_cache"
            ></Check>
            <Message>
              If disabled, Bazarr will use ffprobe to index video file
              properties on each run. This will result in higher disk I/O.
            </Message>
          </Input>
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
