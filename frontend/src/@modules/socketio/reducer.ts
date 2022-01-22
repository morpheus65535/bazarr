import { ActionCreator } from "@reduxjs/toolkit";
import { QueryKeys } from "apis/queries/keys";
import {
  siteAddNotifications,
  siteAddProgress,
  siteRemoveProgress,
  siteUpdateInitialization,
  siteUpdateOffline,
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
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Series, id]);
        });
      },
      delete: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Series, id]);
        });
      },
    },
    {
      key: "movie",
      update: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Movies, id]);
        });
      },
      delete: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Movies, id]);
        });
      },
    },
    {
      key: "episode",
      update: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Episodes, id]);
        });
      },
      delete: (ids) => {
        ids.forEach((id) => {
          queryClient.invalidateQueries([QueryKeys.Episodes, id]);
        });
      },
    },
    {
      key: "episode-wanted",
      update: (ids) => {
        // Find a better way to update wanted
        queryClient.invalidateQueries([QueryKeys.Episodes, QueryKeys.Wanted]);
      },
      delete: () => {
        queryClient.invalidateQueries([QueryKeys.Episodes, QueryKeys.Wanted]);
      },
    },
    {
      key: "movie-wanted",
      update: (ids) => {
        // Find a better way to update wanted
        queryClient.invalidateQueries([QueryKeys.Movies, QueryKeys.Wanted]);
      },
      delete: () => {
        queryClient.invalidateQueries([QueryKeys.Movies, QueryKeys.Wanted]);
      },
    },
    {
      key: "settings",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.System]);
      },
    },
    {
      key: "languages",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.System, QueryKeys.Languages]);
      },
    },
    {
      key: "badges",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.System, QueryKeys.Badges]);
      },
    },
    {
      key: "movie-history",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.Movies, QueryKeys.History]);
      },
    },
    {
      key: "movie-blacklist",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.Movies, QueryKeys.Blacklist]);
      },
    },
    {
      key: "episode-history",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.Episodes, QueryKeys.History]);
      },
    },
    {
      key: "episode-blacklist",
      any: () => {
        queryClient.invalidateQueries([
          QueryKeys.Episodes,
          QueryKeys.Blacklist,
        ]);
      },
    },
    {
      key: "reset-episode-wanted",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.Episodes, QueryKeys.Wanted]);
      },
    },
    {
      key: "reset-movie-wanted",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.Movies, QueryKeys.Wanted]);
      },
    },
    {
      key: "task",
      any: () => {
        queryClient.invalidateQueries([QueryKeys.System, QueryKeys.Tasks]);
      },
    },
  ];
}
