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
import { useIsMoviesEnabled, useIsSeriesEnabled } from "../@redux/hooks";
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
import SettingsMoviesView from "../Settings/Movies";
import SettingsNotificationsView from "../Settings/Notifications";
import SettingsProvidersView from "../Settings/Providers";
import SettingsSchedulerView from "../Settings/Scheduler";
import SettingsSeriesView from "../Settings/Series";
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
import RootRedirect from "./RootRedirect";

export function useNavigationItems() {
  const seriesEnabled = useIsSeriesEnabled();
  const moviesEnabled = useIsMoviesEnabled();
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
        enabled: seriesEnabled,
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
        enabled: moviesEnabled,
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
            enabled: seriesEnabled,
            component: SeriesHistoryView,
          },
          {
            name: "Movies",
            path: "/movies",
            enabled: moviesEnabled,
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
            enabled: seriesEnabled,
            component: BlacklistSeriesView,
          },
          {
            name: "Movies",
            path: "/movies",
            enabled: moviesEnabled,
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
            enabled: seriesEnabled,
            component: WantedSeriesView,
          },
          {
            name: "Movies",
            path: "/movies",
            badge: movies,
            enabled: moviesEnabled,
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
            name: "Series",
            path: "/series",
            component: SettingsSeriesView,
          },
          {
            name: "Movies",
            path: "/movies",
            component: SettingsMoviesView,
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
            badge: providers,
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
    [episodes, movies, providers, moviesEnabled, seriesEnabled]
  );

  return items;
}
