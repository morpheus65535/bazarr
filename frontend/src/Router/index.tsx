import { FunctionComponent, lazy, useMemo } from "react";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router";
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
import SeriesView from "@/pages/Series";
import SettingsApplicationView from "@/pages/Settings/Application";
import SettingsGeneralView from "@/pages/Settings/General";
import SettingsIntegrationsView from "@/pages/Settings/Integrations";
import SettingsJellyfinView from "@/pages/Settings/Jellyfin";
import SettingsLanguagesGeneralView from "@/pages/Settings/Languages/General";
import SettingsLanguagesLayout from "@/pages/Settings/Languages/Layout";
import SettingsLanguageMappingsView from "@/pages/Settings/Languages/Mappings";
import SettingsLanguageProfilesView from "@/pages/Settings/Languages/Profiles";
import SettingsLibraryView from "@/pages/Settings/Library";
import SettingsMaintenanceView from "@/pages/Settings/Maintenance";
import SettingsNotificationsView from "@/pages/Settings/Notifications";
import SettingsPlexView from "@/pages/Settings/Plex";
import SettingsProvidersAdvancedView from "@/pages/Settings/Providers/Advanced";
import SettingsProvidersLayout from "@/pages/Settings/Providers/Layout";
import SettingsProvidersMetadataView from "@/pages/Settings/Providers/Metadata";
import SettingsProvidersProtectionView from "@/pages/Settings/Providers/Protection";
import SettingsProvidersSubtitlesView from "@/pages/Settings/Providers/Subtitles";
import SettingsProvidersTranslationView from "@/pages/Settings/Providers/Translation";
import SettingsRadarrView from "@/pages/Settings/Radarr";
import SettingsSchedulerView from "@/pages/Settings/Scheduler";
import SettingsSonarrView from "@/pages/Settings/Sonarr";
import SettingsSubtitleProcessingView from "@/pages/Settings/SubtitleProcessing";
import SettingsSubtitlesFilesView from "@/pages/Settings/Subtitles/Files";
import SettingsSubtitlesLayout from "@/pages/Settings/Subtitles/Layout";
import SettingsSubtitlesSearchView from "@/pages/Settings/Subtitles/Search";
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
import { RouterItemContext } from "./useRouteItems";

const HistoryStats = lazy(
  () => import("@/pages/History/Statistics/HistoryStats"),
);
const SystemStatusView = lazy(() => import("@/pages/System/Status"));

const useRoutes = (): CustomRouteObject[] => {
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
                path: "library",
                name: "Library",
                element: <SettingsLibraryView></SettingsLibraryView>,
                children: [
                  {
                    index: true,
                    element: <Navigate to="sonarr" replace></Navigate>,
                  },
                  {
                    path: "sonarr",
                    name: "Sonarr",
                    hidden: true,
                    element: <SettingsSonarrView></SettingsSonarrView>,
                  },
                  {
                    path: "radarr",
                    name: "Radarr",
                    hidden: true,
                    element: <SettingsRadarrView></SettingsRadarrView>,
                  },
                ],
              },
              {
                path: "integrations",
                name: "Integrations",
                element: <SettingsIntegrationsView></SettingsIntegrationsView>,
                children: [
                  {
                    index: true,
                    element: <Navigate to="plex" replace></Navigate>,
                  },
                  {
                    path: "plex",
                    name: "Plex",
                    hidden: true,
                    element: <SettingsPlexView></SettingsPlexView>,
                  },
                  {
                    path: "jellyfin",
                    name: "Jellyfin",
                    hidden: true,
                    element: <SettingsJellyfinView></SettingsJellyfinView>,
                  },
                  {
                    path: "sonarr",
                    hidden: true,
                    element: (
                      <Navigate
                        to="/settings/library/sonarr"
                        replace
                      ></Navigate>
                    ),
                  },
                  {
                    path: "radarr",
                    hidden: true,
                    element: (
                      <Navigate
                        to="/settings/library/radarr"
                        replace
                      ></Navigate>
                    ),
                  },
                ],
              },
              {
                path: "languages",
                name: "Languages",
                element: <SettingsLanguagesLayout></SettingsLanguagesLayout>,
                children: [
                  {
                    index: true,
                    element: <Navigate to="general" replace></Navigate>,
                  },
                  {
                    path: "general",
                    name: "Selection",
                    hidden: true,
                    element: (
                      <SettingsLanguagesGeneralView></SettingsLanguagesGeneralView>
                    ),
                  },
                  {
                    path: "mappings",
                    name: "Mappings",
                    hidden: true,
                    element: (
                      <SettingsLanguageMappingsView></SettingsLanguageMappingsView>
                    ),
                  },
                  {
                    path: "profiles",
                    name: "Profiles",
                    hidden: true,
                    element: (
                      <SettingsLanguageProfilesView></SettingsLanguageProfilesView>
                    ),
                  },
                ],
              },
              {
                path: "providers",
                name: "Providers",
                element: <SettingsProvidersLayout></SettingsProvidersLayout>,
                children: [
                  {
                    index: true,
                    element: <Navigate to="subtitles" replace></Navigate>,
                  },
                  {
                    path: "subtitles",
                    name: "Subtitles",
                    hidden: true,
                    element: (
                      <SettingsProvidersSubtitlesView></SettingsProvidersSubtitlesView>
                    ),
                  },
                  {
                    path: "translation",
                    name: "Translation",
                    hidden: true,
                    element: (
                      <SettingsProvidersTranslationView></SettingsProvidersTranslationView>
                    ),
                  },
                  {
                    path: "protection",
                    name: "Protection",
                    hidden: true,
                    element: (
                      <SettingsProvidersProtectionView></SettingsProvidersProtectionView>
                    ),
                  },
                  {
                    path: "metadata",
                    name: "Metadata",
                    hidden: true,
                    element: (
                      <SettingsProvidersMetadataView></SettingsProvidersMetadataView>
                    ),
                  },
                  {
                    path: "advanced",
                    name: "Advanced",
                    hidden: true,
                    element: (
                      <SettingsProvidersAdvancedView></SettingsProvidersAdvancedView>
                    ),
                  },
                ],
              },
              {
                path: "subtitles",
                name: "Subtitles",
                element: <SettingsSubtitlesLayout></SettingsSubtitlesLayout>,
                children: [
                  {
                    index: true,
                    element: <Navigate to="files" replace></Navigate>,
                  },
                  {
                    path: "files",
                    name: "Files",
                    hidden: true,
                    element: (
                      <SettingsSubtitlesFilesView></SettingsSubtitlesFilesView>
                    ),
                  },
                  {
                    path: "search",
                    name: "Search",
                    hidden: true,
                    element: (
                      <SettingsSubtitlesSearchView></SettingsSubtitlesSearchView>
                    ),
                  },
                  {
                    path: "processing",
                    name: "Processing",
                    hidden: true,
                    element: (
                      <SettingsSubtitleProcessingView></SettingsSubtitleProcessingView>
                    ),
                  },
                  {
                    path: "general",
                    hidden: true,
                    element: (
                      <Navigate
                        to="/settings/subtitles/files"
                        replace
                      ></Navigate>
                    ),
                  },
                  {
                    path: "translation",
                    hidden: true,
                    element: (
                      <Navigate
                        to="/settings/providers/translation"
                        replace
                      ></Navigate>
                    ),
                  },
                ],
              },
              {
                path: "notifications",
                name: "Notifications",
                element: (
                  <SettingsNotificationsView></SettingsNotificationsView>
                ),
              },
              {
                path: "application",
                name: "Application",
                element: <SettingsApplicationView></SettingsApplicationView>,
                children: [
                  {
                    index: true,
                    element: <Navigate to="general" replace></Navigate>,
                  },
                  {
                    path: "general",
                    name: "General",
                    hidden: true,
                    element: <SettingsGeneralView></SettingsGeneralView>,
                  },
                  {
                    path: "ui",
                    name: "UI",
                    hidden: true,
                    element: <SettingsUIView></SettingsUIView>,
                  },
                  {
                    path: "scheduler",
                    name: "Scheduler",
                    hidden: true,
                    element: <SettingsSchedulerView></SettingsSchedulerView>,
                  },
                  {
                    path: "maintenance",
                    name: "Maintenance",
                    hidden: true,
                    element: (
                      <SettingsMaintenanceView></SettingsMaintenanceView>
                    ),
                  },
                ],
              },
              {
                path: "sonarr",
                hidden: true,
                element: (
                  <Navigate to="/settings/library/sonarr" replace></Navigate>
                ),
              },
              {
                path: "radarr",
                hidden: true,
                element: (
                  <Navigate to="/settings/library/radarr" replace></Navigate>
                ),
              },
              {
                path: "plex",
                hidden: true,
                element: (
                  <Navigate to="/settings/integrations/plex" replace></Navigate>
                ),
              },
              {
                path: "jellyfin",
                hidden: true,
                element: (
                  <Navigate
                    to="/settings/integrations/jellyfin"
                    replace
                  ></Navigate>
                ),
              },
              {
                path: "general",
                hidden: true,
                element: (
                  <Navigate
                    to="/settings/application/general"
                    replace
                  ></Navigate>
                ),
              },
              {
                path: "ui",
                hidden: true,
                element: (
                  <Navigate to="/settings/application/ui" replace></Navigate>
                ),
              },
              {
                path: "scheduler",
                hidden: true,
                element: (
                  <Navigate
                    to="/settings/application/scheduler"
                    replace
                  ></Navigate>
                ),
              },
              {
                path: "maintenance",
                hidden: true,
                element: (
                  <Navigate
                    to="/settings/application/maintenance"
                    replace
                  ></Navigate>
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
