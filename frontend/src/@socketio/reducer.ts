import {
  badgeUpdateAll,
  episodeUpdateBy,
  episodeUpdateById,
  movieUpdateBlacklist,
  movieUpdateHistoryList,
  movieUpdateList,
  movieUpdateWantedList,
  seriesUpdateBlacklist,
  seriesUpdateHistoryList,
  seriesUpdateList,
  siteUpdateOffline,
  systemUpdateLanguagesAll,
  systemUpdateSettings,
} from "../@redux/actions";
import { createCombineAction } from "../@redux/actions/factory";
import reduxStore from "../@redux/store";
import { ActionDispatcher } from "../@redux/types";

function wrapToOptionalId(fn: (id: number[]) => ActionDispatcher<any>) {
  return createCombineAction((ids?: number[]) => {
    const actions: ActionDispatcher<any>[] = [];
    if (ids !== undefined) {
      actions.push(fn(ids));
    }
    return actions;
  });
}

function bindToReduxStore(fn: (ids?: number[]) => any): SocketIO.ActionFn {
  return (ids?: number[]) => reduxStore.dispatch(fn(ids));
}

export const SocketIOReducer: SocketIO.Reducer[] = [
  {
    key: "connect",
    any: () => reduxStore.dispatch(siteUpdateOffline(false)),
  },
  {
    key: "disconnect",
    any: () => reduxStore.dispatch(siteUpdateOffline(true)),
  },
  {
    key: "episode-blacklist",
    state: (s) => s.series.blacklist,
    any: bindToReduxStore(seriesUpdateBlacklist),
  },
  {
    key: "episode-history",
    state: (s) => s.series.historyList,
    any: bindToReduxStore(seriesUpdateHistoryList),
  },
  {
    key: "episode-wanted",
    state: (s) => s.series.wantedEpisodesList,
    update: bindToReduxStore(wrapToOptionalId(episodeUpdateById)),
  },
  {
    key: "movie-blacklist",
    state: (s) => s.movie.blacklist,
    any: bindToReduxStore(movieUpdateBlacklist),
  },
  {
    key: "movie-history",
    state: (s) => s.movie.historyList,
    any: bindToReduxStore(movieUpdateHistoryList),
  },
  {
    key: "movie-wanted",
    state: (s) => s.movie.wantedMovieList,
    update: bindToReduxStore(wrapToOptionalId(movieUpdateWantedList)),
  },
  {
    key: "series",
    state: (s) => s.series.seriesList,
    update: bindToReduxStore(seriesUpdateList),
  },
  {
    key: "series",
    state: (s) => s.series.episodeList,
    update: bindToReduxStore(wrapToOptionalId(episodeUpdateBy)),
  },
  {
    key: "movie",
    state: (s) => s.movie.movieList,
    update: bindToReduxStore(movieUpdateList),
  },
  {
    key: "episode",
    state: (s) => s.series.episodeList,
    update: bindToReduxStore(wrapToOptionalId(episodeUpdateById)),
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
