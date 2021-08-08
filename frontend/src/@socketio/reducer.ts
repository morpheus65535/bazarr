import { ActionCreator } from "@reduxjs/toolkit";
import {
  movieRemoveById,
  movieRemoveWantedById,
  movieUpdateById,
  movieUpdateWantedById,
  seriesRemoveById,
  seriesRemoveWantedById,
  seriesUpdateById,
  seriesUpdateWantedById,
  siteAddNotifications,
  siteAddProgress,
  siteBootstrap,
  siteRemoveProgress,
  siteUpdateBadges,
  siteUpdateInitialization,
  siteUpdateOffline,
  systemUpdateAllSettings,
  systemUpdateLanguages,
} from "../@redux/actions";
import reduxStore from "../@redux/store";

export function bindReduxAction<T extends ActionCreator<any>>(action: T) {
  return (...args: Parameters<T>) => {
    reduxStore.dispatch(action(...args));
  };
}

export function bindReduxActionWithParam<T extends ActionCreator<any>>(
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
      delete: (ids) => {
        setTimeout(() => {
          ids.forEach((id) => {
            reduxStore.dispatch(siteRemoveProgress(id));
          });
        }, 3 * 1000);
      },
    },
    {
      key: "series",
      update: bindReduxAction(seriesUpdateById),
      delete: bindReduxAction(seriesRemoveById),
    },
    {
      key: "movie",
      update: bindReduxAction(movieUpdateById),
      delete: bindReduxAction(movieRemoveById),
    },
    {
      key: "episode-wanted",
      update: bindReduxAction(seriesUpdateWantedById),
      delete: bindReduxAction(seriesRemoveWantedById),
    },
    {
      key: "movie-wanted",
      update: bindReduxAction(movieUpdateWantedById),
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
  ];
}
