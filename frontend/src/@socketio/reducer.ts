import { createAction } from "redux-actions";
import {
  badgeUpdateAll,
  bootstrap,
  movieDeleteItems,
  movieUpdateList,
  seriesDeleteItems,
  seriesUpdateList,
  siteAddNotifications,
  siteAddProgress,
  siteInitializationFailed,
  siteRemoveProgress,
  siteUpdateOffline,
  systemUpdateLanguagesAll,
  systemUpdateSettings,
} from "../@redux/actions";
import reduxStore from "../@redux/store";

function bindToReduxStore(
  fn: (ids?: number[]) => any
): SocketIO.ActionFn<number> {
  return (ids?: number[]) => reduxStore.dispatch(fn(ids));
}

export function createDeleteAction(type: string): SocketIO.ActionFn<number> {
  return createAction(type, (id?: number[]) => id ?? []);
}

export function createDefaultReducer(): SocketIO.Reducer[] {
  return [
    {
      key: "connect",
      any: () => reduxStore.dispatch(siteUpdateOffline(false)),
    },
    {
      key: "connect",
      any: () => reduxStore.dispatch<any>(bootstrap()),
    },
    {
      key: "connect_error",
      any: () => {
        const initialized = reduxStore.getState().site.initialized;
        if (initialized === true) {
          reduxStore.dispatch(siteUpdateOffline(true));
        } else {
          reduxStore.dispatch(siteInitializationFailed());
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
          const notifications = msg.map<ReduxStore.Notification>((message) => ({
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
      update: bindToReduxStore(seriesUpdateList),
      delete: bindToReduxStore(seriesDeleteItems),
    },
    {
      key: "movie",
      update: bindToReduxStore(movieUpdateList),
      delete: bindToReduxStore(movieDeleteItems),
    },
    {
      key: "settings",
      any: bindToReduxStore(systemUpdateSettings),
    },
    {
      key: "languages",
      any: bindToReduxStore(systemUpdateLanguagesAll),
    },
    {
      key: "badges",
      any: bindToReduxStore(badgeUpdateAll),
    },
  ];
}
