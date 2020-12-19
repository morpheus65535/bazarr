import { AsyncAction } from "../types";
import {
  UPDATE_MOVIE_HISTORY_LIST,
  UPDATE_MOVIE_LIST,
  UPDATE_MOVIE_WANTED_LIST,
  UPDATE_MOVIE_INFO,
} from "../constants";

import { mapToAsyncState, updateAsyncList } from "./mapper";

import { handleActions } from "redux-actions";

const reducer = handleActions<MovieState, any>(
  {
    [UPDATE_MOVIE_LIST]: {
      next(state, action: AsyncAction<Movie[]>) {
        return {
          ...state,
          movieList: mapToAsyncState(action, state.movieList.items),
        };
      },
    },
    [UPDATE_MOVIE_WANTED_LIST]: {
      next(state, action: AsyncAction<WantedMovie[]>) {
        return {
          ...state,
          wantedMovieList: mapToAsyncState(action, state.wantedMovieList.items),
        };
      },
    },
    [UPDATE_MOVIE_HISTORY_LIST]: {
      next(state, action: AsyncAction<MovieHistory[]>) {
        return {
          ...state,
          historyList: mapToAsyncState(action, state.historyList.items),
        };
      },
    },
    [UPDATE_MOVIE_INFO]: {
      next(state, action: AsyncAction<Movie[]>) {
        return {
          ...state,
          movieList: updateAsyncList(action, state.movieList, "radarrId"),
        };
      },
    },
  },
  {
    movieList: { updating: false, items: [] },
    wantedMovieList: { updating: false, items: [] },
    historyList: { updating: false, items: [] },
  }
);

export default reducer;
