import { handleActions } from "redux-actions";
import {
  MOVIES_UPDATE_BLACKLIST,
  MOVIES_UPDATE_HISTORY_LIST,
  MOVIES_UPDATE_INFO,
  MOVIES_UPDATE_LIST,
  MOVIES_UPDATE_WANTED_LIST,
} from "../constants";
import { AsyncAction } from "../types";
import { mapToAsyncState, updateAsyncList } from "./mapper";

const reducer = handleActions<MovieState, any>(
  {
    [MOVIES_UPDATE_LIST]: {
      next(state, action: AsyncAction<Movie[]>) {
        return {
          ...state,
          movieList: mapToAsyncState(action, state.movieList.items),
        };
      },
    },
    [MOVIES_UPDATE_WANTED_LIST]: {
      next(state, action: AsyncAction<WantedMovie[]>) {
        return {
          ...state,
          wantedMovieList: mapToAsyncState(action, state.wantedMovieList.items),
        };
      },
    },
    [MOVIES_UPDATE_HISTORY_LIST]: {
      next(state, action: AsyncAction<MovieHistory[]>) {
        return {
          ...state,
          historyList: mapToAsyncState(action, state.historyList.items),
        };
      },
    },
    [MOVIES_UPDATE_INFO]: {
      next(state, action: AsyncAction<Movie[]>) {
        return {
          ...state,
          movieList: updateAsyncList(action, state.movieList, "radarrId"),
        };
      },
    },
    [MOVIES_UPDATE_BLACKLIST]: {
      next(state, action: AsyncAction<MovieBlacklist[]>) {
        return {
          ...state,
          blacklist: mapToAsyncState(action, state.blacklist.items),
        };
      },
    },
  },
  {
    movieList: { updating: true, items: [] },
    wantedMovieList: { updating: true, items: [] },
    historyList: { updating: true, items: [] },
    blacklist: { updating: true, items: [] },
  }
);

export default reducer;
