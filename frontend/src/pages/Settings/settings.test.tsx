import { http } from "msw";
import { HttpResponse } from "msw";
import server from "@/tests/mocks/node";
import { renderTest, RenderTestCase } from "@/tests/render";
import SettingsGeneralView from "./General";
import SettingsJellyfinView from "./Jellyfin";
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
    setupEach: () => {
      server.use(
        http.get("/api/system/languages", () => {
          return HttpResponse.json({});
        }),
      );
      server.use(
        http.get("/api/system/languages/profiles", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
      server.use(
        http.get("/api/system/status", () => {
          return HttpResponse.json({});
        }),
      );
    },
  },
  {
    name: "notifications page",
    ui: SettingsNotificationsView,
    setupEach: () => {
      server.use(
        http.get("/api/system/settings", () => {
          return HttpResponse.json({
            general: {
              theme: "auto",
            },
            notifications: {
              providers: [],
            },
          });
        }),
      );
    },
  },
  {
    name: "providers page",
    ui: SettingsProvidersView,
  },
  {
    name: "radarr page",
    ui: SettingsRadarrView,
    setupEach: () => {
      server.use(
        http.get("/api/system/settings", () => {
          return HttpResponse.json({
            general: {
              theme: "auto",
            },
            radarr: {
              base_url: "/radarr",
            },
          });
        }),
      );
    },
  },
  {
    name: "jellyfin page",
    ui: SettingsJellyfinView,
  },
  {
    name: "scheduler page",
    ui: SettingsSchedulerView,
  },
  {
    name: "sonarr page",
    ui: SettingsSonarrView,
    setupEach: () => {
      server.use(
        http.get("/api/system/settings", () => {
          return HttpResponse.json({
            general: {
              theme: "auto",
            },
            sonarr: {
              base_url: "/sonarr",
            },
          });
        }),
      );
    },
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
