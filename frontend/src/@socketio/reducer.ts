import {
  badgeUpdateAll,
  movieUpdateList,
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
      key: "disconnect",
      any: () => reduxStore.dispatch(siteUpdateOffline(true)),
    },
    {
      key: "series",
      state: (s) => s.series.seriesList,
      update: bindToReduxStore(seriesUpdateList),
    },
    {
      key: "movie",
      state: (s) => s.movie.movieList,
      update: bindToReduxStore(movieUpdateList),
    },
    {
      key: "settings",
      state: (s) => s.system.settings,
      any: bindToReduxStore(systemUpdateSettings),
    },
    {
      key: "languages",
      state: (s) => s.system.languages,
      any: bindToReduxStore(systemUpdateLanguagesAll),
    },
    {
      key: "badges",
      any: bindToReduxStore(badgeUpdateAll),
    },
  ];
}
