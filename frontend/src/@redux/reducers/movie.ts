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
  movieUpdateHistoryByRange,
  movieUpdateWantedById,
  movieUpdateWantedByRange,
} from "../actions";
import { AsyncUtility } from "../utils";
import {
  createAsyncEntityReducer,
  createAsyncItemReducer,
} from "../utils/factory";

interface Movie {
  movieList: Async.Entity<Item.Movie>;
  wantedMovieList: Async.Entity<Wanted.Movie>;
  historyList: Async.Entity<History.Movie>;
  blacklist: Async.Item<Blacklist.Movie[]>;
}

const defaultMovie: Movie = {
  movieList: AsyncUtility.getDefaultEntity("radarrId"),
  wantedMovieList: AsyncUtility.getDefaultEntity("radarrId"),
  historyList: AsyncUtility.getDefaultEntity("id"),
  blacklist: AsyncUtility.getDefaultItem(),
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

  createAsyncEntityReducer(builder, (s) => s.historyList, {
    range: movieUpdateHistoryByRange,
    dirty: movieMarkHistoryDirty,
  });

  createAsyncItemReducer(builder, (s) => s.blacklist, {
    all: movieUpdateBlacklist,
    dirty: movieMarkBlacklistDirty,
  });
});

export default reducer;
