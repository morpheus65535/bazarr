import {} from "socket.io-client";
import {
  badgeUpdateAll,
  movieUpdateBlacklist,
  movieUpdateHistoryList,
  seriesUpdateBlacklist,
  seriesUpdateHistoryList,
  systemUpdateTasks,
} from "../../@redux/actions";

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
    update: () => systemUpdateTasks,
  },
];
