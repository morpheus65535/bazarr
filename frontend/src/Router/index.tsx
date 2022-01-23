import App from "@/App";
import NotFound from "@/pages/404";
import BlacklistMoviesView from "@/pages/Blacklist/Movies";
import BlacklistSeriesView from "@/pages/Blacklist/Series";
import Episodes from "@/pages/Episodes";
import MoviesHistoryView from "@/pages/History/Movies";
import SeriesHistoryView from "@/pages/History/Series";
import MovieView from "@/pages/Movies";
import MovieDetail from "@/pages/Movies/Details";
import SeriesView from "@/pages/Series";
import SettingsGeneralView from "@/pages/Settings/General";
import SettingsLanguagesView from "@/pages/Settings/Languages";
import SettingsNotificationsView from "@/pages/Settings/Notifications";
import SettingsProvidersView from "@/pages/Settings/Providers";
import SettingsRadarrView from "@/pages/Settings/Radarr";
import SettingsSchedulerView from "@/pages/Settings/Scheduler";
import SettingsSonarrView from "@/pages/Settings/Sonarr";
import SettingsSubtitlesView from "@/pages/Settings/Subtitles";
import SettingsUIView from "@/pages/Settings/UI";
import SystemLogsView from "@/pages/System/Logs";
import SystemProvidersView from "@/pages/System/Providers";
import SystemReleasesView from "@/pages/System/Releases";
import SystemStatusView from "@/pages/System/Status";
import SystemTasksView from "@/pages/System/Tasks";
import WantedMoviesView from "@/pages/Wanted/Movies";
import WantedSeriesView from "@/pages/Wanted/Series";
import React from "react";
import Navigator from "./Navigator";
import { Route } from "./type";

export const routes: Route[] = [
  {
    path: "/",
    element: <App></App>,
    children: [
      {
        index: true,
        element: <Navigator></Navigator>,
      },
      {
        path: "/series",
        children: [
          {
            index: true,
            element: <SeriesView></SeriesView>,
          },
          {
            path: ":id",
            element: <Episodes></Episodes>,
          },
        ],
      },
      {
        path: "/movies",
        children: [
          {
            index: true,
            element: <MovieView></MovieView>,
          },
          {
            path: ":id",
            element: <MovieDetail></MovieDetail>,
          },
        ],
      },
      {
        path: "/history",
        children: [
          {
            path: "series",
            element: <SeriesHistoryView></SeriesHistoryView>,
          },
          {
            path: "movies",
            element: <MoviesHistoryView></MoviesHistoryView>,
          },
        ],
      },
      {
        path: "/blacklist",
        children: [
          {
            path: "series",
            element: <BlacklistSeriesView></BlacklistSeriesView>,
          },
          {
            path: "movies",
            element: <BlacklistMoviesView></BlacklistMoviesView>,
          },
        ],
      },
      {
        path: "/wanted",
        children: [
          {
            path: "series",
            element: <WantedSeriesView></WantedSeriesView>,
          },
          {
            path: "movies",
            element: <WantedMoviesView></WantedMoviesView>,
          },
        ],
      },
      {
        path: "/settings",
        children: [
          {
            path: "general",
            element: <SettingsGeneralView></SettingsGeneralView>,
          },
          {
            path: "languages",
            element: <SettingsLanguagesView></SettingsLanguagesView>,
          },
          {
            path: "providers",
            element: <SettingsProvidersView></SettingsProvidersView>,
          },
          {
            path: "subtitles",
            element: <SettingsSubtitlesView></SettingsSubtitlesView>,
          },
          {
            path: "sonarr",
            element: <SettingsSonarrView></SettingsSonarrView>,
          },
          {
            path: "radarr",
            element: <SettingsRadarrView></SettingsRadarrView>,
          },
          {
            path: "notifications",
            element: <SettingsNotificationsView></SettingsNotificationsView>,
          },
          {
            path: "scheduler",
            element: <SettingsSchedulerView></SettingsSchedulerView>,
          },
          {
            path: "ui",
            element: <SettingsUIView></SettingsUIView>,
          },
        ],
      },
      {
        path: "/system",
        children: [
          {
            path: "tasks",
            element: <SystemTasksView></SystemTasksView>,
          },
          {
            path: "logs",
            element: <SystemLogsView></SystemLogsView>,
          },
          {
            path: "providers",
            element: <SystemProvidersView></SystemProvidersView>,
          },
          {
            path: "status",
            element: <SystemStatusView></SystemStatusView>,
          },
          {
            path: "releases",
            element: <SystemReleasesView></SystemReleasesView>,
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <NotFound></NotFound>,
  },
];
