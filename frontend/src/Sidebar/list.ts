import { SidebarDefinition } from "./types";
import {
  faPlay,
  faFilm,
  faExclamationTriangle,
  faCogs,
  faLaptop,
  faClock,
  faFileExcel,
} from "@fortawesome/free-solid-svg-icons";

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
        name: "Schedular",
        link: "/settings/schedular",
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
    ],
  },
];
