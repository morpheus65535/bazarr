import { createReducer } from "@reduxjs/toolkit";
import {
  movieMarkBlacklistDirty,
  movieMarkDirtyById,
  movieMarkHistoryDirty,
  movieMarkWantedDirtyById,
  movieRemoveById,
  movieRemoveWantedById,
  movieUpdateAll,
  movieUpdateBlacklist,
  movieUpdateById,
  movieUpdateByRange,
  movieUpdateHistory,
  movieUpdateWantedById,
  movieUpdateWantedByRange,
} from "../actions";
import { AsyncUtility } from "../utils/async";
import {
  createAsyncEntityReducer,
  createAsyncListReducer,
} from "../utils/factory";

interface Movie {
  movieList: Async.Entity<Item.Movie>;
  wantedMovieList: Async.Entity<Wanted.Movie>;
  historyList: Async.List<History.Movie>;
  blacklist: Async.List<Blacklist.Movie>;
}

const defaultMovie: Movie = {
  movieList: AsyncUtility.getDefaultEntity("radarrId"),
  wantedMovieList: AsyncUtility.getDefaultEntity("radarrId"),
  historyList: AsyncUtility.getDefaultList(),
  blacklist: AsyncUtility.getDefaultList(),
};

const reducer = createReducer(defaultMovie, (builder) => {
  createAsyncEntityReducer(builder, (s) => s.movieList, {
    range: movieUpdateByRange,
    ids: movieUpdateById,
    removeIds: movieRemoveById,
    all: movieUpdateAll,
    dirty: movieMarkDirtyById,
  });

  createAsyncEntityReducer(builder, (s) => s.wantedMovieList, {
    range: movieUpdateWantedByRange,
    ids: movieUpdateWantedById,
    removeIds: movieRemoveWantedById,
    dirty: movieMarkWantedDirtyById,
  });

  createAsyncListReducer(builder, (s) => s.historyList, "raw_timestamp", {
    all: movieUpdateHistory,
    allDirty: movieMarkHistoryDirty,
  });

  createAsyncListReducer(builder, (s) => s.blacklist, "timestamp", {
    all: movieUpdateBlacklist,
    allDirty: movieMarkBlacklistDirty,
  });
});

export default reducer;
