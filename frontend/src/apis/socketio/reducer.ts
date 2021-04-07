import {
  badgeUpdateAll,
  episodeUpdateBy,
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
    update: () =>
      createAsyncCombineAction((id?: number[]) => {
        const actions: AsyncActionDispatcher<any>[] = [seriesUpdateList(id)];
        if (id !== undefined) {
          actions.push(episodeUpdateBy(id));
        }
        return actions;
      }),
  },
  {
    key: "movie",
    state: (s) => s.movie.movieList,
    update: () => movieUpdateList,
  },
  {
    key: "episode",
    state: (s) => s.series.episodeList,
    // TODO
    // update: () => episodeUpdateBy
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
