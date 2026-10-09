import { FunctionComponent, useMemo } from "react";
import { Box, Text as MantineText } from "@mantine/core";
import { SelectorOption } from "@/components";
import {
  Check,
  CollapseBox,
  File,
  Layout,
  Message,
  Number,
  Section,
  Selector,
} from "@/pages/Settings/components";
import {
  backupOptions,
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
    <Layout name="Scheduler">
      <Section header="Sonarr/Radarr Sync">
        <Selector
          label="Sync with Sonarr"
          options={seriesSyncOptions}
          settingKey="settings-sonarr-series_sync"
        ></Selector>
        <Selector
          label="Sync with Radarr"
          options={moviesSyncOptions}
          settingKey="settings-radarr-movies_sync"
        ></Selector>
      </Section>
      <Section header="Disk Indexing">
        <Selector
          label="Update All Episode Subtitles from Disk"
          settingKey="settings-sonarr-full_update"
          options={diskUpdateOptions}
        ></Selector>

        <CollapseBox
          settingKey="settings-sonarr-full_update"
          on={(k) => k === "Weekly"}
        >
          <Selector
            label="Day of Week"
            settingKey="settings-sonarr-full_update_day"
            options={dayOptions}
          ></Selector>
        </CollapseBox>
        <CollapseBox
          settingKey="settings-sonarr-full_update"
          on={(k) => k === "Daily" || k === "Weekly"}
        >
          <Selector
            label="Time of Day"
            settingKey="settings-sonarr-full_update_hour"
            options={timeOptions}
          ></Selector>
        </CollapseBox>

        <Check
          label="Use cached embedded subtitles parser results"
          settingKey="settings-sonarr-use_ffprobe_cache"
        ></Check>
        <Message>
          If disabled, Bazarr will use the embedded subtitles parser to index
          episodes file properties on each run. This will result in higher disk
          I/O.
        </Message>

        <Selector
          label="Update All Movie Subtitles from Disk"
          settingKey="settings-radarr-full_update"
          options={diskUpdateOptions}
        ></Selector>

        <CollapseBox
          settingKey="settings-radarr-full_update"
          on={(k) => k === "Weekly"}
        >
          <Selector
            label="Day of Week"
            settingKey="settings-radarr-full_update_day"
            options={dayOptions}
          ></Selector>
        </CollapseBox>
        <CollapseBox
          settingKey="settings-radarr-full_update"
          on={(k) => k === "Daily" || k === "Weekly"}
        >
          <Selector
            label="Time of Day"
            settingKey="settings-radarr-full_update_hour"
            options={timeOptions}
          ></Selector>
        </CollapseBox>

        <Check
          label="Use cached embedded subtitles parser results"
          settingKey="settings-radarr-use_ffprobe_cache"
        ></Check>
        <Message>
          If disabled, Bazarr will use embedded subtitles parser to index movies
          file properties on each run. This will result in higher disk I/O.
        </Message>
      </Section>
      <Section header="Search and Upgrade Subtitles">
        <Selector
          label="Search for Missing Series Subtitles"
          settingKey="settings-general-wanted_search_frequency"
          options={upgradeOptions}
        ></Selector>

        <Selector
          label="Search for Missing Movies Subtitles"
          options={upgradeOptions}
          settingKey="settings-general-wanted_search_frequency_movie"
        ></Selector>

        <Selector
          label="Upgrade Previously Downloaded Subtitles"
          options={upgradeOptions}
          settingKey="settings-general-upgrade_frequency"
        ></Selector>
      </Section>
      <Section header="Backups">
        <File
          label="Folder"
          settingKey="settings-backup-folder"
          type="bazarr"
        ></File>
        <Message>Absolute path to the backup directory</Message>
        <Number
          label="Retention"
          settingKey="settings-backup-retention"
          rightSection={
            <Box w="4rem" style={{ justifyContent: "flex-end" }}>
              <MantineText size="xs" px="sm" c="dimmed">
                Days
              </MantineText>
            </Box>
          }
        ></Number>
        <Selector
          label="Backup Database and Configuration File"
          settingKey="settings-backup-frequency"
          options={backupOptions}
        ></Selector>

        <CollapseBox
          settingKey="settings-backup-frequency"
          on={(k) => k === "Weekly"}
        >
          <Selector
            label="Day of Week"
            settingKey="settings-backup-day"
            options={dayOptions}
          ></Selector>
        </CollapseBox>
        <CollapseBox
          settingKey="settings-backup-frequency"
          on={(k) => k === "Daily" || k === "Weekly"}
        >
          <Selector
            label="Time of Day"
            settingKey="settings-backup-hour"
            options={timeOptions}
          ></Selector>
        </CollapseBox>
      </Section>
    </Layout>
  );
};

export default SettingsSchedulerView;
