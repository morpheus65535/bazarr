import { createReducer } from "@reduxjs/toolkit";
import {
  movieRemoveItems,
  movieRemoveWantedItems,
  movieUpdateAll,
  movieUpdateBlacklist,
  movieUpdateByRange,
  movieUpdateHistoryList,
  movieUpdateList,
  movieUpdateWantedByRange,
  movieUpdateWantedList,
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
  createAsyncEntityReducer(
    builder,
    (s) => s.movieList,
    movieUpdateByRange,
    movieUpdateList,
    movieRemoveItems,
    movieUpdateAll
  );

  createAsyncEntityReducer(
    builder,
    (s) => s.wantedMovieList,
    movieUpdateWantedByRange,
    movieUpdateWantedList,
    movieRemoveWantedItems
  );

  createAsyncListReducer(builder, movieUpdateHistoryList, (s) => s.historyList);
  createAsyncListReducer(builder, movieUpdateBlacklist, (s) => s.blacklist);
});

export default reducer;
