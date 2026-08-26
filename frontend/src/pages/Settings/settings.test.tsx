import { http } from "msw";
import { HttpResponse } from "msw";
import server from "@/tests/mocks/node";
import { renderTest, RenderTestCase } from "@/tests/render";
import SettingsLanguagesGeneralView from "./Languages/General";
import SettingsLanguageMappingsView from "./Languages/Mappings";
import SettingsLanguageProfilesView from "./Languages/Profiles";
import SettingsGeneralView from "./General";
import SettingsJellyfinView from "./Jellyfin";
import SettingsMaintenanceView from "./Maintenance";
import SettingsNotificationsView from "./Notifications";
import SettingsProvidersView from "./Providers";
import SettingsRadarrView from "./Radarr";
import SettingsSchedulerView from "./Scheduler";
import SettingsSonarrView from "./Sonarr";
import SettingsSubtitleProcessingView from "./SubtitleProcessing";
import SettingsSubtitlesView from "./Subtitles";
import SettingsTranslationView from "./Translation";
import SettingsUIView from "./UI";

const languagesSetup = () => {
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
};

const cases: RenderTestCase[] = [
  {
    name: "general page",
    ui: SettingsGeneralView,
    setupEach: () => {
      server.use(
        http.get("/api/system/status", () => {
          return HttpResponse.json({});
        }),
      );
    },
  },
  {
    name: "languages general page",
    ui: SettingsLanguagesGeneralView,
    setupEach: languagesSetup,
  },
  {
    name: "languages mappings page",
    ui: SettingsLanguageMappingsView,
    setupEach: languagesSetup,
  },
  {
    name: "languages profiles page",
    ui: SettingsLanguageProfilesView,
    setupEach: languagesSetup,
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
    name: "maintenance page",
    ui: SettingsMaintenanceView,
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
    name: "subtitle processing page",
    ui: SettingsSubtitleProcessingView,
  },
  {
    name: "translation page",
    ui: SettingsTranslationView,
  },
  {
    name: "ui page",
    ui: SettingsUIView,
  },
];

renderTest("Settings", cases);
