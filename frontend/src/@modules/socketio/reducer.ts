import { ActionCreator } from "@reduxjs/toolkit";
import {
  episodesMarkBlacklistDirty,
  episodesMarkDirtyById,
  episodesRemoveById,
  episodesResetHistory,
  movieMarkBlacklistDirty,
  movieMarkDirtyById,
  movieMarkWantedDirtyById,
  movieRemoveById,
  movieRemoveWantedById,
  movieResetHistory,
  movieResetWanted,
  seriesMarkDirtyById,
  seriesMarkWantedDirtyById,
  seriesRemoveById,
  seriesRemoveWantedById,
  seriesResetWanted,
  siteAddNotifications,
  siteAddProgress,
  siteRemoveProgress,
  siteUpdateInitialization,
  siteUpdateOffline,
  systemMarkTasksDirty,
} from "../../@redux/actions";
import reduxStore from "../../@redux/store";
import queryClient from "../../apis/queries";

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
      any: () => {
        // init
        reduxStore.dispatch(siteUpdateInitialization(true));
      },
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
      any: () => {
        queryClient.invalidateQueries("settings");
      },
    },
    {
      key: "languages",
      any: () => {
        queryClient.invalidateQueries("languages");
      },
    },
    {
      key: "badges",
      any: () => {
        queryClient.invalidateQueries("badges");
      },
    },
    {
      key: "movie-history",
      any: bindReduxAction(movieResetHistory),
    },
    {
      key: "movie-blacklist",
      any: bindReduxAction(movieMarkBlacklistDirty),
    },
    {
      key: "episode-history",
      any: bindReduxAction(episodesResetHistory),
    },
    {
      key: "episode-blacklist",
      any: bindReduxAction(episodesMarkBlacklistDirty),
    },
    {
      key: "reset-episode-wanted",
      any: bindReduxAction(seriesResetWanted),
    },
    {
      key: "reset-movie-wanted",
      any: bindReduxAction(movieResetWanted),
    },
    {
      key: "task",
      any: bindReduxAction(systemMarkTasksDirty),
    },
  ];
}
