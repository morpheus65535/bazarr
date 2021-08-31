import {
  faClock,
  faCogs,
  faExclamationTriangle,
  faFileExcel,
  faFilm,
  faLaptop,
  faPlay,
} from "@fortawesome/free-solid-svg-icons";
import { useMemo } from "react";
import { useIsRadarrEnabled, useIsSonarrEnabled } from "../@redux/hooks";
import { useReduxStore } from "../@redux/hooks/base";
import BlacklistMoviesView from "../Blacklist/Movies";
import BlacklistSeriesView from "../Blacklist/Series";
import Episodes from "../DisplayItem/Episodes";
import MovieDetail from "../DisplayItem/MovieDetail";
import MovieView from "../DisplayItem/Movies";
import SeriesView from "../DisplayItem/Series";
import MoviesHistoryView from "../History/Movies";
import SeriesHistoryView from "../History/Series";
import HistoryStats from "../History/Statistics";
import SettingsGeneralView from "../Settings/General";
import SettingsLanguagesView from "../Settings/Languages";
import SettingsNotificationsView from "../Settings/Notifications";
import SettingsProvidersView from "../Settings/Providers";
import SettingsRadarrView from "../Settings/Radarr";
import SettingsSchedulerView from "../Settings/Scheduler";
import SettingsSonarrView from "../Settings/Sonarr";
import SettingsSubtitlesView from "../Settings/Subtitles";
import SettingsUIView from "../Settings/UI";
import EmptyPage, { RouterEmptyPath } from "../special-pages/404";
import SystemLogsView from "../System/Logs";
import SystemProvidersView from "../System/Providers";
import SystemReleasesView from "../System/Releases";
import SystemStatusView from "../System/Status";
import SystemTasksView from "../System/Tasks";
import WantedMoviesView from "../Wanted/Movies";
import WantedSeriesView from "../Wanted/Series";
import { Navigation } from "./nav";

export function useNavigationItems() {
  const sonarr = useIsSonarrEnabled();
  const radarr = useIsRadarrEnabled();
  const { movies, episodes, providers } = useReduxStore((s) => s.site.badges);

  const items = useMemo<Navigation.RouteItem[]>(
    () => [
      {
        name: "404",
        path: RouterEmptyPath,
        component: EmptyPage,
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
            badge: episodes,
            enabled: sonarr,
            component: WantedSeriesView,
          },
          {
            name: "Movies",
            path: "/movies",
            badge: movies,
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
            badge: providers,
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
    [episodes, movies, providers, radarr, sonarr]
  );

  return items;
}
