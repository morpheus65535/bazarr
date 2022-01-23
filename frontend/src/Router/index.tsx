import { useBadges } from "@/apis/hooks";
import App from "@/App";
import Lazy from "@/components/Lazy";
import { useEnabledStatus } from "@/modules/redux/hooks";
import BlacklistMoviesView from "@/pages/Blacklist/Movies";
import BlacklistSeriesView from "@/pages/Blacklist/Series";
import MoviesHistoryView from "@/pages/History/Movies";
import SeriesHistoryView from "@/pages/History/Series";
import MovieView from "@/pages/Movies";
import SeriesView from "@/pages/Series";
import SystemLogsView from "@/pages/System/Logs";
import SystemProvidersView from "@/pages/System/Providers";
import SystemReleasesView from "@/pages/System/Releases";
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

const HistoryStats = React.lazy(() => import("@/pages/History/Statistics"));
const SystemStatusView = React.lazy(() => import("@/pages/System/Status"));
const Authentication = React.lazy(() => import("@/pages/Authentication"));
const NotFound = React.lazy(() => import("@/pages/404"));
const Episodes = React.lazy(() => import("@/pages/Episodes"));
const MovieDetail = React.lazy(() => import("@/pages/Movies/Details"));

const SettingsGeneralView = React.lazy(
  () => import("@/pages/Settings/General")
);
const SettingsLanguagesView = React.lazy(
  () => import("@/pages/Settings/Languages")
);
const SettingsProvidersView = React.lazy(
  () => import("@/pages/Settings/Providers")
);
const SettingsRadarrView = React.lazy(() => import("@/pages/Settings/Radarr"));
const SettingsSonarrView = React.lazy(() => import("@/pages/Settings/Sonarr"));
const SettingsSubtitlesView = React.lazy(
  () => import("@/pages/Settings/Subtitles")
);
const SettingsNotificationsView = React.lazy(
  () => import("@/pages/Settings/Notifications")
);
const SettingsSchedulerView = React.lazy(
  () => import("@/pages/Settings/Scheduler")
);
const SettingsUIView = React.lazy(() => import("@/pages/Settings/UI"));

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
                element: (
                  <Lazy>
                    <Episodes></Episodes>
                  </Lazy>
                ),
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
                element: (
                  <Lazy>
                    <MovieDetail></MovieDetail>
                  </Lazy>
                ),
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
                element: (
                  <Lazy>
                    <HistoryStats></HistoryStats>
                  </Lazy>
                ),
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
                element: (
                  <Lazy>
                    <SettingsGeneralView></SettingsGeneralView>
                  </Lazy>
                ),
              },
              {
                path: "languages",
                name: "Languages",
                element: (
                  <Lazy>
                    <SettingsLanguagesView></SettingsLanguagesView>
                  </Lazy>
                ),
              },
              {
                path: "providers",
                name: "Providers",
                element: (
                  <Lazy>
                    <SettingsProvidersView></SettingsProvidersView>
                  </Lazy>
                ),
              },
              {
                path: "subtitles",
                name: "Subtitles",
                element: (
                  <Lazy>
                    <SettingsSubtitlesView></SettingsSubtitlesView>
                  </Lazy>
                ),
              },
              {
                path: "sonarr",
                name: "Sonarr",
                element: (
                  <Lazy>
                    <SettingsSonarrView></SettingsSonarrView>
                  </Lazy>
                ),
              },
              {
                path: "radarr",
                name: "Radarr",
                element: (
                  <Lazy>
                    <SettingsRadarrView></SettingsRadarrView>
                  </Lazy>
                ),
              },
              {
                path: "notifications",
                name: "Notifications",
                element: (
                  <Lazy>
                    <SettingsNotificationsView></SettingsNotificationsView>
                  </Lazy>
                ),
              },
              {
                path: "scheduler",
                name: "Scheduler",
                element: (
                  <Lazy>
                    <SettingsSchedulerView></SettingsSchedulerView>
                  </Lazy>
                ),
              },
              {
                path: "ui",
                name: "UI",
                element: (
                  <Lazy>
                    <SettingsUIView></SettingsUIView>
                  </Lazy>
                ),
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
                element: (
                  <Lazy>
                    <SystemStatusView></SystemStatusView>
                  </Lazy>
                ),
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
        element: (
          <Lazy>
            <Authentication></Authentication>
          </Lazy>
        ),
      },
      {
        path: "*",
        hidden: true,
        element: (
          <Lazy>
            <NotFound></NotFound>
          </Lazy>
        ),
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
