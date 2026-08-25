import { FunctionComponent, lazy, useMemo } from "react";
import { createBrowserRouter, RouterProvider } from "react-router";
import {
  faClock,
  faCogs,
  faExclamationTriangle,
  faFileExcel,
  faFilm,
  faLaptop,
  faPlay,
  faTrophy,
} from "@fortawesome/free-solid-svg-icons";
import { useBadges } from "@/apis/hooks";
import { useEnabledStatus } from "@/apis/hooks/site";
import App from "@/App";
import { Lazy } from "@/components/async";
import Authentication from "@/pages/Authentication";
import BlacklistMoviesView from "@/pages/Blacklist/Movies";
import BlacklistSeriesView from "@/pages/Blacklist/Series";
import BlacklistSportsView from "@/pages/Blacklist/Sports";
import Episodes from "@/pages/Episodes";
import NotFound from "@/pages/errors/NotFound";
import MoviesHistoryView from "@/pages/History/Movies";
import SeriesHistoryView from "@/pages/History/Series";
import SportsHistoryView from "@/pages/History/Sports";
import MovieView from "@/pages/Movies";
import MovieDetailView from "@/pages/Movies/Details";
import SeriesView from "@/pages/Series";
import SettingsGeneralView from "@/pages/Settings/General";
import SettingsJellyfinView from "@/pages/Settings/Jellyfin";
import SettingsLanguagesView from "@/pages/Settings/Languages";
import SettingsNotificationsView from "@/pages/Settings/Notifications";
import SettingsPlexView from "@/pages/Settings/Plex";
import SettingsProvidersView from "@/pages/Settings/Providers";
import SettingsRadarrView from "@/pages/Settings/Radarr";
import SettingsSchedulerView from "@/pages/Settings/Scheduler";
import SettingsSonarrView from "@/pages/Settings/Sonarr";
import SettingsSportarrView from "@/pages/Settings/Sportarr";
import SettingsSubtitlesView from "@/pages/Settings/Subtitles";
import SettingsUIView from "@/pages/Settings/UI";
import SportsView from "@/pages/Sports";
import SportsEventsView from "@/pages/SportsEvents";
import SystemAnnouncementsView from "@/pages/System/Announcements";
import SystemBackupsView from "@/pages/System/Backups";
import SystemLogsView from "@/pages/System/Logs";
import SystemProvidersView from "@/pages/System/Providers";
import SystemReleasesView from "@/pages/System/Releases";
import SystemTasksView from "@/pages/System/Tasks";
import WantedMoviesView from "@/pages/Wanted/Movies";
import WantedSeriesView from "@/pages/Wanted/Series";
import WantedSportsView from "@/pages/Wanted/Sports";
import { Environment } from "@/utilities";
import Redirector from "./Redirector";
import { RouterNames } from "./RouterNames";
import { CustomRouteObject } from "./type";
import { RouterItemContext } from "./useRouteItems";

const HistoryStats = lazy(
  () => import("@/pages/History/Statistics/HistoryStats"),
);
const SystemStatusView = lazy(() => import("@/pages/System/Status"));

const useRoutes = (): CustomRouteObject[] => {
  const { data } = useBadges();
  const { sonarr, radarr, sportarr } = useEnabledStatus();

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
                path: ":id",
                element: <MovieDetailView></MovieDetailView>,
              },
            ],
          },
          {
            icon: faTrophy,
            name: "Sports",
            path: "sports",
            badge: data?.sportarr_sse,
            hidden: !sportarr,
            children: [
              {
                index: true,
                element: <SportsView></SportsView>,
              },
              {
                path: ":id",
                element: <SportsEventsView></SportsEventsView>,
              },
            ],
          },
          {
            icon: faClock,
            name: "History",
            path: "history",
            hidden: !sonarr && !radarr && !sportarr,
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
                path: "sports",
                name: "Sports",
                hidden: !sportarr,
                element: <SportsHistoryView></SportsHistoryView>,
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
            hidden: !sonarr && !radarr && !sportarr,
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
              {
                name: "Sports",
                path: "sports",
                badge: data?.sports,
                hidden: !sportarr,
                element: <WantedSportsView></WantedSportsView>,
              },
            ],
          },
          {
            icon: faFileExcel,
            name: "Blacklist",
            path: "blacklist",
            hidden: !sonarr && !radarr && !sportarr,
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
              {
                path: "sports",
                name: "Sports",
                hidden: !sportarr,
                element: <BlacklistSportsView></BlacklistSportsView>,
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
                path: "sportarr",
                name: "Sportarr",
                element: <SettingsSportarrView></SettingsSportarrView>,
              },
              {
                path: "plex",
                name: "Plex",
                element: <SettingsPlexView></SettingsPlexView>,
              },
              {
                path: "jellyfin",
                name: "Jellyfin",
                element: <SettingsJellyfinView></SettingsJellyfinView>,
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
      data?.sports,
      data?.sportarr_sse,
      data?.providers,
      data?.sonarr_signalr,
      data?.radarr_signalr,
      data?.announcements,
      data?.status,
      radarr,
      sonarr,
      sportarr,
    ],
  );
};

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
