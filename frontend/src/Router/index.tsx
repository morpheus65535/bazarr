import { useBadges } from "@/apis/hooks";
import App from "@/App";
import { useEnabledStatus } from "@/modules/redux/hooks";
import NotFound from "@/pages/404";
import Authentication from "@/pages/Authentication";
import BlacklistMoviesView from "@/pages/Blacklist/Movies";
import BlacklistSeriesView from "@/pages/Blacklist/Series";
import Episodes from "@/pages/Episodes";
import MoviesHistoryView from "@/pages/History/Movies";
import SeriesHistoryView from "@/pages/History/Series";
import HistoryStats from "@/pages/History/Statistics";
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
import { Environment } from "@/utilities";
import {
  faClock,
  faExclamationTriangle,
  faFileExcel,
  faFilm,
  faLaptop,
  faPlay,
} from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useMemo } from "react";
import { BrowserRouter } from "react-router-dom";
import Redirector from "./Redirector";
import { CustomRouteObject } from "./type";

function useRoutes(): CustomRouteObject[] {
  const { data } = useBadges();
  const { sonarr, radarr } = useEnabledStatus();

  return useMemo(
    () => [
      {
        path: "/",
        element: <App></App>,
        children: [
          {
            index: true,
            element: <Redirector></Redirector>,
          },
          {
            icon: faPlay,
            name: "Series",
            path: "series",
            hidden: !sonarr,
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
            icon: faFilm,
            name: "Movies",
            path: "movies",
            hidden: !radarr,
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
            icon: faClock,
            name: "History",
            path: "history",
            hidden: !sonarr && !radarr,
            children: [
              {
                path: "series",
                name: "Episodes",
                hidden: !sonarr,
                element: <SeriesHistoryView></SeriesHistoryView>,
              },
              {
                path: "movies",
                name: "Movies",
                hidden: !radarr,
                element: <MoviesHistoryView></MoviesHistoryView>,
              },
              {
                path: "stats",
                name: "Statistics",
                element: <HistoryStats></HistoryStats>,
              },
            ],
          },
          {
            icon: faExclamationTriangle,
            name: "Wanted",
            path: "wanted",
            hidden: !sonarr && !radarr,
            children: [
              {
                name: "Episodes",
                path: "series",
                badge: data?.episodes,
                hidden: !sonarr,
                element: <WantedSeriesView></WantedSeriesView>,
              },
              {
                name: "Movies",
                path: "movies",
                badge: data?.movies,
                hidden: !radarr,
                element: <WantedMoviesView></WantedMoviesView>,
              },
            ],
          },
          {
            icon: faFileExcel,
            name: "Blacklist",
            path: "blacklist",
            hidden: !sonarr && !radarr,
            children: [
              {
                path: "series",
                name: "Episodes",
                hidden: !sonarr,
                element: <BlacklistSeriesView></BlacklistSeriesView>,
              },
              {
                path: "movies",
                name: "Movies",
                hidden: !radarr,
                element: <BlacklistMoviesView></BlacklistMoviesView>,
              },
            ],
          },
          {
            icon: faExclamationTriangle,
            name: "Settings",
            path: "settings",
            children: [
              {
                path: "general",
                name: "General",
                element: <SettingsGeneralView></SettingsGeneralView>,
              },
              {
                path: "languages",
                name: "Languages",
                element: <SettingsLanguagesView></SettingsLanguagesView>,
              },
              {
                path: "providers",
                name: "Providers",
                element: <SettingsProvidersView></SettingsProvidersView>,
              },
              {
                path: "subtitles",
                name: "Subtitles",
                element: <SettingsSubtitlesView></SettingsSubtitlesView>,
              },
              {
                path: "sonarr",
                name: "Sonarr",
                element: <SettingsSonarrView></SettingsSonarrView>,
              },
              {
                path: "radarr",
                name: "Radarr",
                element: <SettingsRadarrView></SettingsRadarrView>,
              },
              {
                path: "notifications",
                name: "Notifications",
                element: (
                  <SettingsNotificationsView></SettingsNotificationsView>
                ),
              },
              {
                path: "scheduler",
                name: "Scheduler",
                element: <SettingsSchedulerView></SettingsSchedulerView>,
              },
              {
                path: "ui",
                name: "UI",
                element: <SettingsUIView></SettingsUIView>,
              },
            ],
          },
          {
            icon: faLaptop,
            name: "System",
            path: "system",
            children: [
              {
                path: "tasks",
                name: "Tasks",
                element: <SystemTasksView></SystemTasksView>,
              },
              {
                path: "logs",
                name: "Logs",
                element: <SystemLogsView></SystemLogsView>,
              },
              {
                path: "providers",
                name: "Providers",
                badge: data?.providers,
                element: <SystemProvidersView></SystemProvidersView>,
              },
              {
                path: "status",
                name: "Status",
                element: <SystemStatusView></SystemStatusView>,
              },
              {
                path: "releases",
                name: "Releases",
                element: <SystemReleasesView></SystemReleasesView>,
              },
            ],
          },
        ],
      },
      {
        path: "/login",
        hidden: true,
        element: <Authentication></Authentication>,
      },
      {
        path: "*",
        hidden: true,
        element: <NotFound></NotFound>,
      },
    ],
    [data?.episodes, data?.movies, data?.providers, radarr, sonarr]
  );
}

const RouterItemContext = React.createContext<CustomRouteObject[]>([]);

export const Router: FunctionComponent = ({ children }) => {
  const routes = useRoutes();

  return (
    <RouterItemContext.Provider value={routes}>
      <BrowserRouter basename={Environment.baseUrl}>{children}</BrowserRouter>
    </RouterItemContext.Provider>
  );
};

export function useRouteItems() {
  return React.useContext(RouterItemContext);
}
