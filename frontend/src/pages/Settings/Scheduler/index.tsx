import { FunctionComponent, useMemo } from "react";
import { SelectorOption } from "@/components";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
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
        <Check
          label="Sync Only Monitored Series"
          settingKey={"settings-sonarr-sync_only_monitored_series"}
        ></Check>
        <CollapseBox settingKey={"settings-sonarr-sync_only_monitored_series"}>
          <Message>
            If enabled, only series with a monitored status in Sonarr will be
            synced. If you make changes to a specific unmonitored Sonarr series
            and you want Bazarr to know about those changes, simply toggle the
            monitored status back on in Sonarr and Bazarr will sync any changes.
          </Message>
        </CollapseBox>
        <CollapseBox settingKey={"settings-sonarr-sync_only_monitored_series"}>
          <Check
            label="Sync Only Monitored Episodes"
            settingKey={"settings-sonarr-sync_only_monitored_episodes"}
          ></Check>
          <CollapseBox
            settingKey={"settings-sonarr-sync_only_monitored_episodes"}
          >
            <Message>
              If enabled, only episodes with a monitored status in Sonarr will
              be synced. If you make changes to a specific unmonitored Sonarr
              episode (or season) and you want Bazarr to know about those
              changes, simply toggle the monitored status back on in Sonarr and
              Bazarr will sync any changes. This setting is especially helpful
              for long running TV series with many seasons and many episodes,
              but that are still actively producing new episodes (e.g. Saturday
              Night Live).
            </Message>
          </CollapseBox>
        </CollapseBox>
        <Selector
          label="Sync with Radarr"
          options={moviesSyncOptions}
          settingKey="settings-radarr-movies_sync"
        ></Selector>
        <Check
          label="Sync Only Monitored Movies"
          settingKey={"settings-radarr-sync_only_monitored_movies"}
        ></Check>
        <CollapseBox settingKey={"settings-radarr-sync_only_monitored_movies"}>
          <Message>
            If enabled, only movies with a monitored status in Radarr will be
            synced. If you make changes to a specific unmonitored Radarr movie
            and you want Bazarr to know about those changes, simply toggle the
            monitored status back on in Radarr and Bazarr will sync any changes.
          </Message>
        </CollapseBox>
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
      <Section header="Backup">
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
