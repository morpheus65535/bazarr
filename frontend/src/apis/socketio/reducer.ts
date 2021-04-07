import {
  badgeUpdateAll,
  episodeUpdateBy,
  episodeUpdateById,
  movieUpdateBlacklist,
  movieUpdateHistoryList,
  movieUpdateList,
  seriesUpdateBlacklist,
  seriesUpdateHistoryList,
  seriesUpdateList,
  systemUpdateLanguagesAll,
  systemUpdateSettings,
  systemUpdateTasks,
} from "../../@redux/actions";
import { createAsyncCombineAction } from "../../@redux/actions/factory";
import { AsyncActionDispatcher } from "../../@redux/types";

const episodeUpdateBySeriesWrap = createAsyncCombineAction(
  (seriesid?: number[]) => {
    const actions: AsyncActionDispatcher<any>[] = [];
    if (seriesid !== undefined) {
      actions.push(episodeUpdateBy(seriesid));
    }
    return actions;
  }
);

const episodeUpdateByIdWrap = createAsyncCombineAction(
  (episodeid?: number[]) => {
    const actions: AsyncActionDispatcher<any>[] = [];
    if (episodeid !== undefined) {
      actions.push(episodeUpdateById(episodeid));
    }
    return actions;
  }
);

export const SocketIOReducer: SocketIO.Reducer[] = [
  {
    key: "badges",
    update: () => badgeUpdateAll,
  },
  {
    key: "episode-blacklist",
    state: (s) => s.series.blacklist,
    update: () => seriesUpdateBlacklist,
  },
  {
    key: "movie-blacklist",
    state: (s) => s.movie.blacklist,
    update: () => movieUpdateBlacklist,
  },
  {
    key: "episode-history",
    state: (s) => s.series.historyList,
    update: () => seriesUpdateHistoryList,
  },
  {
    key: "movie-history",
    state: (s) => s.movie.historyList,
    update: () => movieUpdateHistoryList,
  },
  {
    key: "task",
    state: (s) => s.system.tasks,
    update: () => systemUpdateTasks,
  },
  {
    key: "series",
    state: (s) => s.series.seriesList,
    update: () => seriesUpdateList,
  },
  {
    key: "series",
    state: (s) => s.series.episodeList,
    update: () => episodeUpdateBySeriesWrap,
  },
  {
    key: "movie",
    state: (s) => s.movie.movieList,
    update: () => movieUpdateList,
  },
  {
    key: "episode",
    state: (s) => s.series.episodeList,
    update: () => episodeUpdateByIdWrap,
  },
  {
    key: "settings",
    state: (s) => s.system.settings,
    update: () => systemUpdateSettings,
  },
  {
    key: "languages",
    state: (s) => s.system.languages,
    update: () => systemUpdateLanguagesAll,
  },
];
