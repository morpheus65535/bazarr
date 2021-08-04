import { createReducer } from "@reduxjs/toolkit";
import {
  movieRemoveItems,
  movieRemoveWantedItems,
  movieUpdateBlacklist,
  movieUpdateHistoryList,
  movieUpdateList,
  movieUpdateWantedList,
} from "../actions";
import { defaultAOS } from "../utils";
import { AsyncUtility } from "../utils/async";
import {
  createAOSReducer,
  createAOSWholeReducer,
  createAsyncListReducer,
  removeOrderListItem,
} from "../utils/factory";

interface Movie {
  movieList: AsyncOrderState<Item.Movie>;
  wantedMovieList: AsyncOrderState<Wanted.Movie>;
  historyList: Async.List<History.Movie>;
  blacklist: Async.List<Blacklist.Movie>;
}

const defaultMovie: Movie = {
  movieList: defaultAOS(),
  wantedMovieList: defaultAOS(),
  historyList: AsyncUtility.getDefaultList(),
  blacklist: AsyncUtility.getDefaultList(),
};

const reducer = createReducer(defaultMovie, (builder) => {
  createAOSWholeReducer(
    builder,
    movieUpdateList,
    (s) => s.movieList,
    "radarrId"
  );

  createAOSReducer(
    builder,
    movieUpdateWantedList,
    (s) => s.wantedMovieList,
    "radarrId"
  );

  createAsyncListReducer(builder, movieUpdateHistoryList, (s) => s.historyList);
  createAsyncListReducer(builder, movieUpdateBlacklist, (s) => s.blacklist);

  builder
    .addCase(movieRemoveWantedItems, (state, action) => {
      removeOrderListItem(state.wantedMovieList, action);
    })
    .addCase(movieRemoveItems, (state, action) => {
      removeOrderListItem(state.movieList, action);
    });
});

export default reducer;
