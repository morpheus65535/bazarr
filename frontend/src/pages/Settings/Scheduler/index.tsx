import { SelectorOption } from "@/components";
import { FunctionComponent, useMemo } from "react";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Section,
  Selector,
} from "../components";
import {
  backupOptions,
  dayOptions,
  diskUpdateOptions,
  episodesSyncOptions,
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
          label="Update Series List from Sonarr"
          options={seriesSyncOptions}
          settingKey="settings-sonarr-series_sync"
        ></Selector>

        <Selector
          label="Update Episodes List from Sonarr"
          options={episodesSyncOptions}
          settingKey="settings-sonarr-episodes_sync"
        ></Selector>

        <Selector
          label="Update Movies List from Radarr"
          options={moviesSyncOptions}
          settingKey="settings-radarr-movies_sync"
        ></Selector>
      </Section>
      <Section header="Disk Indexing">
        <Selector
          label="Update all Episode Subtitles from Disk"
          settingKey="settings-sonarr-full_update"
          options={diskUpdateOptions}
        ></Selector>

        <CollapseBox
          settingKey="settings-sonarr-full_update"
          on={(k) => k === "Weekly"}
        >
          <Selector
            label="Day of The Week"
            settingKey="settings-sonarr-full_update_day"
            options={dayOptions}
          ></Selector>
        </CollapseBox>
        <CollapseBox
          settingKey="settings-sonarr-full_update"
          on={(k) => k === "Daily" || k === "Weekly"}
        >
          <Selector
            label="Time of The Day"
            settingKey="settings-sonarr-full_update_hour"
            options={timeOptions}
          ></Selector>
        </CollapseBox>

        <Check
          label="Use cached ffprobe results"
          settingKey="settings-sonarr-use_ffprobe_cache"
        ></Check>
        <Message>
          If disabled, Bazarr will use ffprobe to index video file properties on
          each run. This will result in higher disk I/O.
        </Message>

        <Selector
          label="Update all Movie Subtitles from Disk"
          settingKey="settings-radarr-full_update"
          options={diskUpdateOptions}
        ></Selector>

        <CollapseBox
          settingKey="settings-radarr-full_update"
          on={(k) => k === "Weekly"}
        >
          <Selector
            label="Day of The Week"
            settingKey="settings-radarr-full_update_day"
            options={dayOptions}
          ></Selector>
        </CollapseBox>
        <CollapseBox
          settingKey="settings-radarr-full_update"
          on={(k) => k === "Daily" || k === "Weekly"}
        >
          <Selector
            label="Time of The Day"
            settingKey="settings-radarr-full_update_hour"
            options={timeOptions}
          ></Selector>
        </CollapseBox>

        <Check
          label="Use cached ffprobe results"
          settingKey="settings-radarr-use_ffprobe_cache"
        ></Check>
        <Message>
          If disabled, Bazarr will use ffprobe to index video file properties on
          each run. This will result in higher disk I/O.
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
      <Section header="Backup">
        <Selector
          label="Backup config and database"
          settingKey="settings-backup-frequency"
          options={backupOptions}
        ></Selector>

        <CollapseBox
          settingKey="settings-backup-frequency"
          on={(k) => k === "Weekly"}
        >
          <Selector
            label="Day of The Week"
            settingKey="settings-backup-day"
            options={dayOptions}
          ></Selector>
        </CollapseBox>
        <CollapseBox
          settingKey="settings-backup-frequency"
          on={(k) => k === "Daily" || k === "Weekly"}
        >
          <Selector
            label="Time of The Day"
            settingKey="settings-backup-hour"
            options={timeOptions}
          ></Selector>
        </CollapseBox>
      </Section>
    </Layout>
  );
};

export default SettingsSchedulerView;
