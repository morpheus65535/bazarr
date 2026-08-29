import { http } from "msw";
import { HttpResponse } from "msw";
import server from "@/tests/mocks/node";
import { renderTest, RenderTestCase } from "@/tests/render";
import SettingsLanguagesGeneralView from "./Languages/General";
import SettingsLanguageMappingsView from "./Languages/Mappings";
import SettingsLanguageProfilesView from "./Languages/Profiles";
import SettingsProvidersAdvancedView from "./Providers/Advanced";
import SettingsProvidersMetadataView from "./Providers/Metadata";
import SettingsProvidersProtectionView from "./Providers/Protection";
import SettingsProvidersSubtitlesView from "./Providers/Subtitles";
import SettingsProvidersTranslationView from "./Providers/Translation";
import SettingsSubtitlesFilesView from "./Subtitles/Files";
import SettingsSubtitlesSearchView from "./Subtitles/Search";
import SettingsGeneralView from "./General";
import SettingsJellyfinView from "./Jellyfin";
import SettingsMaintenanceView from "./Maintenance";
import SettingsNotificationsView from "./Notifications";
import SettingsRadarrView from "./Radarr";
import SettingsSchedulerView from "./Scheduler";
import SettingsSonarrView from "./Sonarr";
import SettingsSubtitleProcessingView from "./SubtitleProcessing";
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
    name: "providers subtitles page",
    ui: SettingsProvidersSubtitlesView,
  },
  {
    name: "providers translation page",
    ui: SettingsProvidersTranslationView,
  },
  {
    name: "providers protection page",
    ui: SettingsProvidersProtectionView,
  },
  {
    name: "providers metadata page",
    ui: SettingsProvidersMetadataView,
  },
  {
    name: "providers advanced page",
    ui: SettingsProvidersAdvancedView,
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
    name: "subtitles files page",
    ui: SettingsSubtitlesFilesView,
  },
  {
    name: "subtitles search page",
    ui: SettingsSubtitlesSearchView,
  },
  {
    name: "subtitle processing page",
    ui: SettingsSubtitleProcessingView,
  },
  {
    name: "ui page",
    ui: SettingsUIView,
  },
];

renderTest("Settings", cases);
