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
  systemUpdateLanguagesAll,
  systemUpdateSettings,
  systemUpdateTasks,
} from "../../@redux/actions";
import { createCombineAction } from "../../@redux/actions/factory";
import { ActionDispatcher } from "../../@redux/types";

function wrapToOptionalId(fn: (id: number[]) => ActionDispatcher<any>) {
  return createCombineAction((ids?: number[]) => {
    const actions: ActionDispatcher<any>[] = [];
    if (ids !== undefined) {
      actions.push(fn(ids));
    }
    return actions;
  });
}

export const SocketIOReducer: SocketIO.Reducer[] = [
  {
    key: "episode-blacklist",
    state: (s) => s.series.blacklist,
    update: () => seriesUpdateBlacklist,
  },
  {
    key: "episode-history",
    state: (s) => s.series.historyList,
    update: () => seriesUpdateHistoryList,
  },
  {
    key: "episode-wanted",
    state: (s) => s.series.wantedEpisodesList,
    update: () => wrapToOptionalId(episodeUpdateById),
  },
  {
    key: "movie-blacklist",
    state: (s) => s.movie.blacklist,
    any: () => movieUpdateBlacklist,
  },
  {
    key: "movie-history",
    state: (s) => s.movie.historyList,
    any: () => movieUpdateHistoryList,
  },
  {
    key: "movie-wanted",
    state: (s) => s.movie.wantedMovieList,
    update: () => wrapToOptionalId(movieUpdateWantedList),
  },
  {
    key: "series",
    state: (s) => s.series.seriesList,
    update: () => seriesUpdateList,
  },
  {
    key: "series",
    state: (s) => s.series.episodeList,
    update: () => wrapToOptionalId(episodeUpdateBy),
  },
  {
    key: "movie",
    state: (s) => s.movie.movieList,
    update: () => movieUpdateList,
  },
  {
    key: "episode",
    state: (s) => s.series.episodeList,
    update: () => wrapToOptionalId(episodeUpdateById),
  },
  {
    key: "settings",
    state: (s) => s.system.settings,
    any: () => systemUpdateSettings,
  },
  {
    key: "languages",
    state: (s) => s.system.languages,
    any: () => systemUpdateLanguagesAll,
  },
  {
    key: "task",
    state: (s) => s.system.tasks,
    any: () => systemUpdateTasks,
  },
  {
    key: "badges",
    any: () => badgeUpdateAll,
  },
];
