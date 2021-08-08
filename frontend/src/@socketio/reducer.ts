import { ActionCreatorWithPayload, AsyncThunk } from "@reduxjs/toolkit";
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

function bindToReduxStore(
  fn: (ids?: number[]) => any
): SocketIO.ActionFn<number> {
  return (ids?: number[]) => reduxStore.dispatch(fn(ids));
}

function bindToReduxStoreOptional(fn: ActionCreatorWithPayload<number[]>) {
  return (ids?: number[]) => {
    if (ids !== undefined) {
      reduxStore.dispatch(fn(ids));
    }
  };
}

function bindToReduxStoreAsyncOptional<S>(fn: AsyncThunk<S, number[], {}>) {
  return (ids?: number[]) => {
    if (ids !== undefined) {
      reduxStore.dispatch(fn(ids));
    }
  };
}

export function createDefaultReducer(): SocketIO.Reducer[] {
  return [
    {
      key: "connect",
      any: () => reduxStore.dispatch(siteUpdateOffline(false)),
    },
    {
      key: "connect",
      any: () => reduxStore.dispatch(siteBootstrap()),
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
      any: () => reduxStore.dispatch(siteUpdateOffline(true)),
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
      update: (progress) => {
        if (progress) {
          reduxStore.dispatch(siteAddProgress(progress));
        }
      },
      delete: (ids) => {
        setTimeout(() => {
          ids?.forEach((id) => {
            reduxStore.dispatch(siteRemoveProgress(id));
          });
        }, 3 * 1000);
      },
    },
    {
      key: "series",
      update: bindToReduxStoreAsyncOptional(seriesUpdateById),
      delete: bindToReduxStoreOptional(seriesRemoveById),
    },
    {
      key: "movie",
      update: bindToReduxStoreAsyncOptional(movieUpdateById),
      delete: bindToReduxStoreOptional(movieRemoveById),
    },
    {
      key: "episode-wanted",
      update: (ids: number[] | undefined) => {
        if (ids) {
          reduxStore.dispatch(seriesUpdateWantedById(ids) as any);
        }
      },
      delete: bindToReduxStoreOptional(seriesRemoveWantedById),
    },
    {
      key: "movie-wanted",
      update: (ids: number[] | undefined) => {
        if (ids) {
          reduxStore.dispatch(movieUpdateWantedById(ids) as any);
        }
      },
      delete: bindToReduxStoreOptional(movieRemoveWantedById),
    },
    {
      key: "settings",
      any: bindToReduxStore(systemUpdateAllSettings),
    },
    {
      key: "languages",
      any: bindToReduxStore(systemUpdateLanguages),
    },
    {
      key: "badges",
      any: bindToReduxStore(siteUpdateBadges),
    },
  ];
}
