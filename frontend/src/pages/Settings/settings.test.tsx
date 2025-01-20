import { http } from "msw";
import { HttpResponse } from "msw";
import server from "@/tests/mocks/node";
import { renderTest, RenderTestCase } from "@/tests/render";
import SettingsGeneralView from "./General";
import SettingsLanguagesView from "./Languages";
import SettingsProvidersView from "./Providers";
import SettingsSchedulerView from "./Scheduler";
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
    },
  },
  // TODO: Test Notifications Page
  {
    name: "providers page",
    ui: SettingsProvidersView,
  },
  // TODO: Test Radarr Page
  {
    name: "scheduler page",
    ui: SettingsSchedulerView,
  },
  // TODO: Test Sonarr Page
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
