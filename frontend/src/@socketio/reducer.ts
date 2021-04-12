import {
  badgeUpdateAll,
  movieUpdateList,
  movieUpdateWantedList,
  seriesUpdateList,
  seriesUpdateWantedList,
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
      key: "episode-wanted",
      state: (s) => s.series.wantedEpisodesList,
      update: bindToReduxStore(wrapToOptionalId(seriesUpdateWantedList)),
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
