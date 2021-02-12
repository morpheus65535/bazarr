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

export const SidebarList: SidebarDefinition[] = [
  {
    icon: faPlay,
    name: "Series",
    link: "/series",
  },
  {
    icon: faFilm,
    name: "Movies",
    link: "/movies",
  },
  {
    icon: faClock,
    name: "History",
    children: [
      {
        name: "Series",
        link: "/history/series",
      },
      {
        name: "Movies",
        link: "/history/movies",
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
      },
      {
        name: "Movies",
        link: "/blacklist/movies",
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
      },
      {
        name: "Movies",
        link: "/wanted/movies",
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
        name: "Providers",
        link: "/settings/providers",
      },
      {
        name: "Notifications",
        link: "/settings/notifications",
      },
      {
        name: "Schedular",
        link: "/settings/schedular",
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
