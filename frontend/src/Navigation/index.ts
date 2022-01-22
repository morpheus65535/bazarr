import {
  faClock,
  faCogs,
  faExclamationTriangle,
  faFileExcel,
  faFilm,
  faLaptop,
  faPlay,
} from "@fortawesome/free-solid-svg-icons";
import { useIsRadarrEnabled, useIsSonarrEnabled } from "@redux/hooks";
import { useBadges } from "apis/hooks";
import BlacklistMoviesView from "pages/Blacklist/Movies";
import BlacklistSeriesView from "pages/Blacklist/Series";
import Episodes from "pages/Episodes";
import MoviesHistoryView from "pages/History/Movies";
import SeriesHistoryView from "pages/History/Series";
import HistoryStats from "pages/History/Statistics";
import MovieView from "pages/Movies";
import MovieDetail from "pages/Movies/Details";
import SeriesView from "pages/Series";
import SettingsGeneralView from "pages/Settings/General";
import SettingsLanguagesView from "pages/Settings/Languages";
import SettingsNotificationsView from "pages/Settings/Notifications";
import SettingsProvidersView from "pages/Settings/Providers";
import SettingsRadarrView from "pages/Settings/Radarr";
import SettingsSchedulerView from "pages/Settings/Scheduler";
import SettingsSonarrView from "pages/Settings/Sonarr";
import SettingsSubtitlesView from "pages/Settings/Subtitles";
import SettingsUIView from "pages/Settings/UI";
import SystemLogsView from "pages/System/Logs";
import SystemProvidersView from "pages/System/Providers";
import SystemReleasesView from "pages/System/Releases";
import SystemStatusView from "pages/System/Status";
import SystemTasksView from "pages/System/Tasks";
import WantedMoviesView from "pages/Wanted/Movies";
import WantedSeriesView from "pages/Wanted/Series";
import { useMemo } from "react";
import EmptyPage, { RouterEmptyPath } from "special-pages/404";
import { Navigation } from "./nav";
import RootRedirect from "./RootRedirect";

export function useNavigationItems() {
  const sonarr = useIsSonarrEnabled();
  const radarr = useIsRadarrEnabled();
  const { data } = useBadges();

  const items = useMemo<Navigation.RouteItem[]>(
    () => [
      {
        name: "404",
        path: RouterEmptyPath,
        component: EmptyPage,
        routeOnly: true,
      },
      {
        name: "Redirect",
        path: "/",
        component: RootRedirect,
        routeOnly: true,
      },
      {
        icon: faPlay,
        name: "Series",
        path: "/series",
        component: SeriesView,
        enabled: sonarr,
        routes: [
          {
            name: "Episode",
            path: "/:id",
            component: Episodes,
            routeOnly: true,
          },
        ],
      },
      {
        icon: faFilm,
        name: "Movies",
        path: "/movies",
        component: MovieView,
        enabled: radarr,
        routes: [
          {
            name: "Movie Details",
            path: "/:id",
            component: MovieDetail,
            routeOnly: true,
          },
        ],
      },
      {
        icon: faClock,
        name: "History",
        path: "/history",
        routes: [
          {
            name: "Series",
            path: "/series",
            enabled: sonarr,
            component: SeriesHistoryView,
          },
          {
            name: "Movies",
            path: "/movies",
            enabled: radarr,
            component: MoviesHistoryView,
          },
          {
            name: "Statistics",
            path: "/stats",
            component: HistoryStats,
          },
        ],
      },
      {
        icon: faFileExcel,
        name: "Blacklist",
        path: "/blacklist",
        routes: [
          {
            name: "Series",
            path: "/series",
            enabled: sonarr,
            component: BlacklistSeriesView,
          },
          {
            name: "Movies",
            path: "/movies",
            enabled: radarr,
            component: BlacklistMoviesView,
          },
        ],
      },
      {
        icon: faExclamationTriangle,
        name: "Wanted",
        path: "/wanted",
        routes: [
          {
            name: "Series",
            path: "/series",
            badge: data?.episodes,
            enabled: sonarr,
            component: WantedSeriesView,
          },
          {
            name: "Movies",
            path: "/movies",
            badge: data?.movies,
            enabled: radarr,
            component: WantedMoviesView,
          },
        ],
      },
      {
        icon: faCogs,
        name: "Settings",
        path: "/settings",
        routes: [
          {
            name: "General",
            path: "/general",
            component: SettingsGeneralView,
          },
          {
            name: "Languages",
            path: "/languages",
            component: SettingsLanguagesView,
          },
          {
            name: "Providers",
            path: "/providers",
            component: SettingsProvidersView,
          },
          {
            name: "Subtitles",
            path: "/subtitles",
            component: SettingsSubtitlesView,
          },
          {
            name: "Sonarr",
            path: "/sonarr",
            component: SettingsSonarrView,
          },
          {
            name: "Radarr",
            path: "/radarr",
            component: SettingsRadarrView,
          },
          {
            name: "Notifications",
            path: "/notifications",
            component: SettingsNotificationsView,
          },
          {
            name: "Scheduler",
            path: "/scheduler",
            component: SettingsSchedulerView,
          },
          {
            name: "UI",
            path: "/ui",
            component: SettingsUIView,
          },
        ],
      },
      {
        icon: faLaptop,
        name: "System",
        path: "/system",
        routes: [
          {
            name: "Tasks",
            path: "/tasks",
            component: SystemTasksView,
          },
          {
            name: "Logs",
            path: "/logs",
            component: SystemLogsView,
          },
          {
            name: "Providers",
            path: "/providers",
            badge: data?.providers,
            component: SystemProvidersView,
          },
          {
            name: "Status",
            path: "/status",
            component: SystemStatusView,
          },
          {
            name: "Releases",
            path: "/releases",
            component: SystemReleasesView,
          },
        ],
      },
    ],
    [data, radarr, sonarr]
  );

  return items;
}
