import { createReducer } from "@reduxjs/toolkit";
import {
  movieRemoveItems,
  movieRemoveWantedItems,
  movieUpdateBlacklist,
  movieUpdateHistoryList,
  movieUpdateList,
  movieUpdateWantedList,
} from "../actions";
import { defaultAOS, defaultAS } from "../utils";
import {
  createAOSReducer,
  createAOSWholeReducer,
  createAsyncStateReducer,
  removeOrderListItem,
} from "../utils/factory";

const reducer = createReducer<ReduxStore.Movie>(
  {
    movieList: defaultAOS(),
    wantedMovieList: defaultAOS(),
    historyList: defaultAS([]),
    blacklist: defaultAS([]),
  },
  (builder) => {
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

    createAsyncStateReducer(
      builder,
      movieUpdateHistoryList,
      (s) => s.historyList
    );
    createAsyncStateReducer(builder, movieUpdateBlacklist, (s) => s.blacklist);

    builder
      .addCase(movieRemoveWantedItems, (state, action) => {
        removeOrderListItem(state.wantedMovieList, action);
      })
      .addCase(movieRemoveItems, (state, action) => {
        removeOrderListItem(state.movieList, action);
      });
  }
);

export default reducer;
