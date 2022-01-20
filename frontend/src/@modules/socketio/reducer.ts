import { ActionCreator } from "@reduxjs/toolkit";
import {
  siteAddNotifications,
  siteAddProgress,
  siteRemoveProgress,
  siteUpdateInitialization,
  siteUpdateOffline,
} from "../../@redux/actions";
import reduxStore from "../../@redux/store";
import queryClient from "../../apis/queries";
import {
  createEpisodeId,
  createMovieId,
  createSeriesId,
} from "../../utilities";

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
        const initialized = reduxStore.getState().initialized;
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
      update: (ids) => {
        const queries = ids.map(createSeriesId);
        queryClient.invalidateQueries(queries);
      },
      delete: () => {
        queryClient.invalidateQueries("series");
      },
    },
    {
      key: "movie",
      update: (ids) => {
        const queries = ids.map(createMovieId);
        queryClient.invalidateQueries(queries);
      },
      delete: () => {
        queryClient.invalidateQueries("movies");
      },
    },
    {
      key: "episode",
      update: (ids) => {
        const queries = ids.map(createEpisodeId);
        queryClient.invalidateQueries(queries);
      },
      delete: () => {
        queryClient.invalidateQueries("episodes");
      },
    },
    {
      key: "episode-wanted",
      update: (ids) => {
        // Find a better way to update wanted
        queryClient.invalidateQueries("wanted");
      },
      delete: () => {
        queryClient.invalidateQueries("wanted");
      },
    },
    {
      key: "movie-wanted",
      update: (ids) => {
        // Find a better way to update wanted
        queryClient.invalidateQueries("wanted");
      },
      delete: () => {
        queryClient.invalidateQueries("wanted");
      },
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
      any: () => {
        queryClient.invalidateQueries("history");
      },
    },
    {
      key: "movie-blacklist",
      any: () => {
        queryClient.invalidateQueries("blacklist");
      },
    },
    {
      key: "episode-history",
      any: () => {
        queryClient.invalidateQueries("history");
      },
    },
    {
      key: "episode-blacklist",
      any: () => {
        queryClient.invalidateQueries("blacklist");
      },
    },
    {
      key: "reset-episode-wanted",
      any: () => {
        queryClient.invalidateQueries("wanted");
      },
    },
    {
      key: "reset-movie-wanted",
      any: () => {
        queryClient.invalidateQueries("wanted");
      },
    },
    {
      key: "task",
      any: () => {
        queryClient.invalidateQueries("tasks");
      },
    },
  ];
}
