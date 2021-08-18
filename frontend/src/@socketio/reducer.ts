import { ActionCreator } from "@reduxjs/toolkit";
import {
  episodesMarkBlacklistDirty,
  episodesMarkDirtyById,
  episodesRemoveById,
  movieMarkBlacklistDirty,
  movieMarkDirtyById,
  movieMarkWantedDirtyById,
  movieRemoveById,
  movieRemoveWantedById,
  seriesMarkDirtyById,
  seriesMarkWantedDirtyById,
  seriesRemoveById,
  seriesRemoveWantedById,
  siteAddNotifications,
  siteAddProgress,
  siteBootstrap,
  siteRemoveProgress,
  siteUpdateBadges,
  siteUpdateInitialization,
  siteUpdateOffline,
  systemMarkTasksDirty,
  systemUpdateAllSettings,
  systemUpdateLanguages,
} from "../@redux/actions";
import reduxStore from "../@redux/store";

function bindReduxAction<T extends ActionCreator<any>>(action: T) {
  return (...args: Parameters<T>) => {
    reduxStore.dispatch(action(...args));
  };
}

function bindReduxActionWithParam<T extends ActionCreator<any>>(
  action: T,
  ...param: Parameters<T>
) {
  return () => {
    reduxStore.dispatch(action(...param));
  };
}

export function createDefaultReducer(): SocketIO.Reducer[] {
  return [
    {
      key: "connect",
      any: bindReduxActionWithParam(siteUpdateOffline, false),
    },
    {
      key: "connect",
      any: bindReduxAction(siteBootstrap),
    },
    {
      key: "connect_error",
      any: () => {
        const initialized = reduxStore.getState().site.initialized;
        if (initialized === true) {
          reduxStore.dispatch(siteUpdateOffline(true));
        } else {
          reduxStore.dispatch(siteUpdateInitialization("Socket.IO Error"));
        }
      },
    },
    {
      key: "disconnect",
      any: bindReduxActionWithParam(siteUpdateOffline, true),
    },
    {
      key: "message",
      update: (msg) => {
        if (msg) {
          const notifications = msg.map<Server.Notification>((message) => ({
            message,
            type: "info",
            id: "backend-message",
            timeout: 5 * 1000,
          }));

          reduxStore.dispatch(siteAddNotifications(notifications));
        }
      },
    },
    {
      key: "progress",
      update: bindReduxAction(siteAddProgress),
      delete: bindReduxAction(siteRemoveProgress),
    },
    {
      key: "series",
      update: bindReduxAction(seriesMarkDirtyById),
      delete: bindReduxAction(seriesRemoveById),
    },
    {
      key: "movie",
      update: bindReduxAction(movieMarkDirtyById),
      delete: bindReduxAction(movieRemoveById),
    },
    {
      key: "episode",
      update: bindReduxAction(episodesMarkDirtyById),
      delete: bindReduxAction(episodesRemoveById),
    },
    {
      key: "episode-wanted",
      update: bindReduxAction(seriesMarkWantedDirtyById),
      delete: bindReduxAction(seriesRemoveWantedById),
    },
    {
      key: "movie-wanted",
      update: bindReduxAction(movieMarkWantedDirtyById),
      delete: bindReduxAction(movieRemoveWantedById),
    },
    {
      key: "settings",
      any: bindReduxAction(systemUpdateAllSettings),
    },
    {
      key: "languages",
      any: bindReduxAction(systemUpdateLanguages),
    },
    {
      key: "badges",
      any: bindReduxAction(siteUpdateBadges),
    },
    {
      key: "movie-history",
      // any: bindReduxAction(movieMarkHistoryDirty),
    },
    {
      key: "movie-blacklist",
      any: bindReduxAction(movieMarkBlacklistDirty),
    },
    {
      key: "episode-history",
      // any: bindReduxAction(episodesMarkHistoryDirty),
    },
    {
      key: "episode-blacklist",
      any: bindReduxAction(episodesMarkBlacklistDirty),
    },
    {
      key: "task",
      any: bindReduxAction(systemMarkTasksDirty),
    },
  ];
}
