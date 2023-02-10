import { renderTest, RenderTestCase } from "@/tests/render";
import SettingsGeneralView from "./General";
import SettingsLanguagesView from "./Languages";
import SettingsNotificationsView from "./Notifications";
import SettingsProvidersView from "./Providers";
import SettingsRadarrView from "./Radarr";
import SettingsSchedulerView from "./Scheduler";
import SettingsSonarrView from "./Sonarr";
import SettingsSubtitlesView from "./Subtitles";
import SettingsUIView from "./UI";

const cases: RenderTestCase[] = [
  {
    name: "general page",
    ui: SettingsGeneralView,
  },
  {
    name: "languages page",
    ui: SettingsLanguagesView,
  },
  {
    name: "notifications page",
    ui: SettingsNotificationsView,
  },
  {
    name: "providers page",
    ui: SettingsProvidersView,
  },
  {
    name: "radarr page",
    ui: SettingsRadarrView,
  },
  {
    name: "scheduler page",
    ui: SettingsSchedulerView,
  },
  {
    name: "sonarr page",
    ui: SettingsSonarrView,
  },
  {
    name: "subtitles page",
    ui: SettingsSubtitlesView,
  },
  {
    name: "ui page",
    ui: SettingsUIView,
  },
];

renderTest("Settings", cases);
