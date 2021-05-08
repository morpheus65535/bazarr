import {
  badgeUpdateAll,
  bootstrap,
  movieDeleteItems,
  movieUpdateList,
  seriesDeleteItems,
  seriesUpdateList,
  siteAddNotifications,
  siteRemoveNotifications,
  siteUpdateOffline,
  systemUpdateLanguagesAll,
  systemUpdateSettings,
} from "../@redux/actions";
import reduxStore from "../@redux/store";

function bindToReduxStore(fn: (ids?: number[]) => any): SocketIO.ActionFn {
  return (ids?: number[]) => reduxStore.dispatch(fn(ids));
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
      key: "disconnect",
      any: () => reduxStore.dispatch(siteUpdateOffline(true)),
    },
    {
      key: "message",
      update: (msg?: string[]) => {
        if (msg) {
          const notifications = msg.map<ReduxStore.Notification>((message) => ({
            message,
            type: "info",
            timestamp: new Date(),
          }));

          reduxStore.dispatch(siteAddNotifications(notifications));

          const ts = notifications.map((n) => n.timestamp);
          setTimeout(
            () => reduxStore.dispatch(siteRemoveNotifications(ts)),
            5000
          );
        }
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
