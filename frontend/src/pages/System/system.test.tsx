import SystemAnnouncementsView from "@/pages/System/Announcements";
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
  },
  {
    name: "logs page",
    ui: SystemLogsView,
  },
  {
    name: "providers page",
    ui: SystemProvidersView,
  },
  {
    name: "releases page",
    ui: SystemReleasesView,
  },
  {
    name: "status page",
    ui: SystemStatusView,
  },
  {
    name: "tasks page",
    ui: SystemTasksView,
  },
  {
    name: "announcements page",
    ui: SystemAnnouncementsView,
  },
];

renderTest("System", cases);
