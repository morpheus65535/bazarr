import EmptyPage from "@/pages/404";
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
import { RouteObject } from "react-router";
import Navigator from "./Navigator";

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <Navigator></Navigator>,
  },
  {
    path: "*",
    element: <EmptyPage></EmptyPage>,
  },
  {
    path: "/series",
    element: <SeriesView></SeriesView>,
  },
  {
    path: "/series/:id",
    element: <Episodes></Episodes>,
  },
  {
    path: "/movies",
    element: <MovieView></MovieView>,
  },
  {
    path: "/movies/:id",
    element: <MovieDetail></MovieDetail>,
  },
  {
    path: "/history",
    children: [
      {
        path: "/history/series",
        element: <SeriesHistoryView></SeriesHistoryView>,
      },
      {
        path: "/history/movies",
        element: <MoviesHistoryView></MoviesHistoryView>,
      },
    ],
  },
  {
    path: "/blacklist",
    children: [
      {
        path: "/blacklist/series",
        element: <BlacklistSeriesView></BlacklistSeriesView>,
      },
      {
        path: "/blacklist/movies",
        element: <BlacklistMoviesView></BlacklistMoviesView>,
      },
    ],
  },
  {
    path: "/wanted",
    children: [
      {
        path: "/wanted/series",
        element: <WantedSeriesView></WantedSeriesView>,
      },
      {
        path: "/wanted/movies",
        element: <WantedMoviesView></WantedMoviesView>,
      },
    ],
  },
  {
    path: "/settings",
    children: [
      {
        path: "/settings/general",
        element: <SettingsGeneralView></SettingsGeneralView>,
      },
      {
        path: "/settings/languages",
        element: <SettingsLanguagesView></SettingsLanguagesView>,
      },
      {
        path: "/settings/providers",
        element: <SettingsProvidersView></SettingsProvidersView>,
      },
      {
        path: "/settings/subtitles",
        element: <SettingsSubtitlesView></SettingsSubtitlesView>,
      },
      {
        path: "/settings/sonarr",
        element: <SettingsSonarrView></SettingsSonarrView>,
      },
      {
        path: "/settings/radarr",
        element: <SettingsRadarrView></SettingsRadarrView>,
      },
      {
        path: "/settings/notifications",
        element: <SettingsNotificationsView></SettingsNotificationsView>,
      },
      {
        path: "/settings/scheduler",
        element: <SettingsSchedulerView></SettingsSchedulerView>,
      },
      {
        path: "/settings/ui",
        element: <SettingsUIView></SettingsUIView>,
      },
    ],
  },
  {
    path: "/system",
    children: [
      {
        path: "/system/tasks",
        element: <SystemTasksView></SystemTasksView>,
      },
      {
        path: "/system/logs",
        element: <SystemLogsView></SystemLogsView>,
      },
      {
        path: "/system/providers",
        element: <SystemProvidersView></SystemProvidersView>,
      },
      {
        path: "/system/status",
        element: <SystemStatusView></SystemStatusView>,
      },
      {
        path: "/system/releases",
        element: <SystemReleasesView></SystemReleasesView>,
      },
    ],
  },
];
