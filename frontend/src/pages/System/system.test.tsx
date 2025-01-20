import { http } from "msw";
import { HttpResponse } from "msw";
import SystemAnnouncementsView from "@/pages/System/Announcements";
import server from "@/tests/mocks/node";
import { renderTest, RenderTestCase } from "@/tests/render";
import SystemBackupsView from "./Backups";
import SystemLogsView from "./Logs";
import SystemProvidersView from "./Providers";
import SystemReleasesView from "./Releases";
import SystemStatusView from "./Status";
import SystemTasksView from "./Tasks";

const cases: RenderTestCase[] = [
  {
    name: "backups page",
    ui: SystemBackupsView,
    setupEach: () => {
      server.use(
        http.get("/api/system/backups", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
  {
    name: "logs page",
    ui: SystemLogsView,
    setupEach: () => {
      server.use(
        http.get("/api/system/logs", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
  {
    name: "providers page",
    ui: SystemProvidersView,
    setupEach: () => {
      server.use(
        http.get("/api/providers", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
  {
    name: "releases page",
    ui: SystemReleasesView,
    setupEach: () => {
      server.use(
        http.get("/api/system/releases", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
  {
    name: "status page",
    ui: SystemStatusView,
    setupEach: () => {
      server.use(
        http.get("/api/system/status", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
      server.use(
        http.get("/api/system/health", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
  {
    name: "tasks page",
    ui: SystemTasksView,
    setupEach: () => {
      server.use(
        http.get("/api/system/tasks", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
  {
    name: "announcements page",
    ui: SystemAnnouncementsView,
    setupEach: () => {
      server.use(
        http.get("/api/system/announcements", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
];

renderTest("System", cases);
