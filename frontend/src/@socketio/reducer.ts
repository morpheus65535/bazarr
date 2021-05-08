import {
  badgeUpdateAll,
  bootstrap,
  movieDeleteItems,
  movieUpdateList,
  seriesDeleteItems,
  seriesUpdateList,
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
