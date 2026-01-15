import { FunctionComponent, useMemo } from "react";
import { useSystemStatus } from "@/apis/hooks";
import { SelectorOption } from "@/components";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Number,
  Section,
  Selector,
} from "@/pages/Settings/components";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";
import {
  backupOptions,
  dayOptions,
  diskUpdateOptions,
  moviesSyncOptions,
  seriesSyncOptions,
  upgradeOptions,
} from "./options";

// Child component that can use the settings context (must be inside Layout)
const JobLimitsMessage: FunctionComponent<{
  defaultTotal: number;
  calcLimits: (total: number) => { short: number; long: number; room: number };
}> = ({ defaultTotal, calcLimits }) => {
  const concurrentJobsSetting = useSettingValue<number>(
    "settings-general-concurrent_jobs",
  );
  const total = concurrentJobsSetting ?? defaultTotal;
  const { short, long, room } = calcLimits(total);

  return (
    <Message>
      How many subtitle tasks can run at the same time (capped by actual CPU
      count). Minimum: 2
      <br />
      <br />
      Short: {short} (quick tasks like subtitle downloads)
      <br />
      Long: {long} (slow tasks like Whisper transcription)
      <br />
      Demotion room: {room} (frees short slots when tasks run too long)
      {room === 0 && (
        <>
          <br />
          No room for demotion. Increase concurrent jobs to allow it.
        </>
      )}
    </Message>
  );
};

const SettingsSchedulerView: FunctionComponent = () => {
  const { data: status } = useSystemStatus();

  const timeOptions = useMemo(() => {
    return Array(24)
      .fill(null)
      .map<SelectorOption<number>>((_, idx) => ({
        label: `${idx}:00`,
        value: idx,
      }));
  }, []);

  // Calculate job limits based on CPU cores and user setting
  const jobLimits = useMemo(() => {
    const cpuCores = status?.cpu_cores ?? 2;
    const maxCpu = Math.max(cpuCores, 2);
    const defaultTotal = Math.max(Math.floor(cpuCores / 2), 2);

    // Helper to calculate limits for any total value
    const calcLimits = (total: number) => {
      const short = Math.max(Math.floor(total / 2), 1);
      const long = Math.max(Math.floor(short / 2), 1);
      const room = Math.max(total - short - long, 0);
      return { short, long, room };
    };

    return {
      cpuCount: maxCpu,
      defaultTotal,
      calcLimits,
    };
  }, [status?.cpu_cores]);

  return (
    <Layout name="Scheduler">
      <Section header="Jobs Manager Execution">
        <Number
          label="Max Concurrent Jobs"
          min={2}
          max={jobLimits.cpuCount}
          settingKey="settings-general-concurrent_jobs"
        ></Number>
        <JobLimitsMessage
          defaultTotal={jobLimits.defaultTotal}
          calcLimits={jobLimits.calcLimits}
        />
        <Number
          label="Long Job Threshold (minutes)"
          min={0}
          max={60}
          settingKey="settings-general-long_job_threshold"
        ></Number>
        <Message>
          Jobs exceeding this threshold are demoted to the long queue, freeing a
          short job slot. Set to 0 to disable.
        </Message>
      </Section>
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
