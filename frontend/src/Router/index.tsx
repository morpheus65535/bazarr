import {
  createContext,
  FunctionComponent,
  lazy,
  useContext,
  useMemo,
} from "react";
import { createBrowserRouter, RouterProvider } from "react-router";
import {
  faClock,
  faCogs,
  faExclamationTriangle,
  faFileExcel,
  faFilm,
  faLaptop,
  faPlay,
} from "@fortawesome/free-solid-svg-icons";
import { useBadges } from "@/apis/hooks";
import { useEnabledStatus } from "@/apis/hooks/site";
import App from "@/App";
import { Lazy } from "@/components/async";
import Authentication from "@/pages/Authentication";
import BlacklistMoviesView from "@/pages/Blacklist/Movies";
import BlacklistSeriesView from "@/pages/Blacklist/Series";
import Episodes from "@/pages/Episodes";
import NotFound from "@/pages/errors/NotFound";
import MoviesHistoryView from "@/pages/History/Movies";
import SeriesHistoryView from "@/pages/History/Series";
import MovieView from "@/pages/Movies";
import MovieDetailView from "@/pages/Movies/Details";
import MovieMassEditor from "@/pages/Movies/Editor";
import SeriesView from "@/pages/Series";
import SeriesMassEditor from "@/pages/Series/Editor";
import SettingsGeneralView from "@/pages/Settings/General";
import SettingsLanguagesView from "@/pages/Settings/Languages";
import SettingsNotificationsView from "@/pages/Settings/Notifications";
import SettingsPlexView from "@/pages/Settings/Plex";
import SettingsProvidersView from "@/pages/Settings/Providers";
import SettingsRadarrView from "@/pages/Settings/Radarr";
import SettingsSchedulerView from "@/pages/Settings/Scheduler";
import SettingsSonarrView from "@/pages/Settings/Sonarr";
import SettingsSubtitlesView from "@/pages/Settings/Subtitles";
import SettingsUIView from "@/pages/Settings/UI";
import SystemAnnouncementsView from "@/pages/System/Announcements";
import SystemBackupsView from "@/pages/System/Backups";
import SystemLogsView from "@/pages/System/Logs";
import SystemProvidersView from "@/pages/System/Providers";
import SystemReleasesView from "@/pages/System/Releases";
import SystemTasksView from "@/pages/System/Tasks";
import WantedMoviesView from "@/pages/Wanted/Movies";
import WantedSeriesView from "@/pages/Wanted/Series";
import { Environment } from "@/utilities";
import Redirector from "./Redirector";
import { RouterNames } from "./RouterNames";
import { CustomRouteObject } from "./type";

const HistoryStats = lazy(
  () => import("@/pages/History/Statistics/HistoryStats"),
);
const SystemStatusView = lazy(() => import("@/pages/System/Status"));

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
            badge: data?.sonarr_signalr,
            hidden: !sonarr,
            children: [
              {
                index: true,
                element: <SeriesView></SeriesView>,
              },
              {
                path: "edit",
                hidden: true,
                element: <SeriesMassEditor></SeriesMassEditor>,
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
            badge: data?.radarr_signalr,
            hidden: !radarr,
            children: [
              {
                index: true,
                element: <MovieView></MovieView>,
              },
              {
                path: "edit",
                hidden: true,
                element: <MovieMassEditor></MovieMassEditor>,
              },
              {
                path: ":id",
                element: <MovieDetailView></MovieDetailView>,
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
            icon: faCogs,
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
                path: "plex",
                name: "Plex",
                element: <SettingsPlexView></SettingsPlexView>,
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
                path: "backup",
                name: "Backups",
                element: <SystemBackupsView></SystemBackupsView>,
              },
              {
                path: "status",
                name: "Status",
                badge: data?.status,
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
              {
                path: "announcements",
                name: "Announcements",
                badge: data?.announcements,
                element: <SystemAnnouncementsView></SystemAnnouncementsView>,
              },
            ],
          },
          {
            path: "*",
            hidden: true,
            element: <NotFound></NotFound>,
          },
        ],
      },
      {
        path: RouterNames.Auth,
        hidden: true,
        element: <Authentication></Authentication>,
      },
    ],
    [
      data?.episodes,
      data?.movies,
      data?.providers,
      data?.sonarr_signalr,
      data?.radarr_signalr,
      data?.announcements,
      data?.status,
      radarr,
      sonarr,
    ],
  );
}

const RouterItemContext = createContext<CustomRouteObject[]>([]);

export const Router: FunctionComponent = () => {
  const routes = useRoutes();

  // TODO: Move this outside the function component scope
  const router = useMemo(
    () =>
      createBrowserRouter(routes, {
        basename: Environment.baseUrl,
      }),
    [routes],
  );

  return (
    <RouterItemContext.Provider value={routes}>
      <RouterProvider router={router}></RouterProvider>
    </RouterItemContext.Provider>
  );
};

export function useRouteItems() {
  return useContext(RouterItemContext);
}
