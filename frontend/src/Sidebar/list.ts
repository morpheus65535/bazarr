import {
  faClock,
  faCogs,
  faExclamationTriangle,
  faFileExcel,
  faFilm,
  faLaptop,
  faPlay,
} from "@fortawesome/free-solid-svg-icons";
import { SidebarDefinition } from "./types";

export const SonarrDisabledKey = "sonarr-disabled";
export const RadarrDisabledKey = "radarr-disabled";

export const SidebarList: SidebarDefinition[] = [
  {
    icon: faPlay,
    name: "Series",
    link: "/series",
    hiddenKey: SonarrDisabledKey,
  },
  {
    icon: faFilm,
    name: "Movies",
    link: "/movies",
    hiddenKey: RadarrDisabledKey,
  },
  {
    icon: faClock,
    name: "History",
    children: [
      {
        name: "Series",
        link: "/history/series",
        hiddenKey: SonarrDisabledKey,
      },
      {
        name: "Movies",
        link: "/history/movies",
        hiddenKey: RadarrDisabledKey,
      },
      {
        name: "Statistics",
        link: "/history/stats",
      },
    ],
  },
  {
    icon: faFileExcel,
    name: "Blacklist",
    children: [
      {
        name: "Series",
        link: "/blacklist/series",
        hiddenKey: SonarrDisabledKey,
      },
      {
        name: "Movies",
        link: "/blacklist/movies",
        hiddenKey: RadarrDisabledKey,
      },
    ],
  },
  {
    icon: faExclamationTriangle,
    name: "Wanted",
    children: [
      {
        name: "Series",
        link: "/wanted/series",
        hiddenKey: SonarrDisabledKey,
      },
      {
        name: "Movies",
        link: "/wanted/movies",
        hiddenKey: RadarrDisabledKey,
      },
    ],
  },
  {
    icon: faCogs,
    name: "Settings",
    children: [
      {
        name: "General",
        link: "/settings/general",
      },
      {
        name: "Languages",
        link: "/settings/languages",
      },
      {
        name: "Providers",
        link: "/settings/providers",
      },
      {
        name: "Subtitles",
        link: "/settings/subtitles",
      },
      {
        name: "Sonarr",
        link: "/settings/sonarr",
      },
      {
        name: "Radarr",
        link: "/settings/radarr",
      },
      {
        name: "Notifications",
        link: "/settings/notifications",
      },
      {
        name: "Scheduler",
        link: "/settings/scheduler",
      },
      {
        name: "UI",
        link: "/settings/ui",
      },
    ],
  },
  {
    icon: faLaptop,
    name: "System",
    children: [
      {
        name: "Tasks",
        link: "/system/tasks",
      },
      {
        name: "Logs",
        link: "/system/logs",
      },
      {
        name: "Providers",
        link: "/system/providers",
      },
      {
        name: "Status",
        link: "/system/status",
      },
      {
        name: "Releases",
        link: "/system/releases",
      },
    ],
  },
];
