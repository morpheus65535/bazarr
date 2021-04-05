import { handleActions } from "redux-actions";
import {
  MOVIES_UPDATE_BLACKLIST,
  MOVIES_UPDATE_HISTORY_LIST,
  MOVIES_UPDATE_LIST,
  MOVIES_UPDATE_RANGE,
  MOVIES_UPDATE_WANTED_LIST,
  MOVIES_UPDATE_WANTED_RANGE,
} from "../constants";
import { AsyncAction } from "../types";
import { updateAsyncState, updateOrderIdState } from "./mapper";

const reducer = handleActions<ReduxStore.Movie, any>(
  {
    [MOVIES_UPDATE_WANTED_LIST]: (
      state,
      action: AsyncAction<AsyncDataWrapper<Wanted.Movie>>
    ) => {
      return {
        ...state,
        wantedMovieList: updateOrderIdState(
          action,
          state.wantedMovieList,
          "radarrId"
        ),
      };
    },
    [MOVIES_UPDATE_WANTED_RANGE]: (
      state,
      action: AsyncAction<AsyncDataWrapper<Wanted.Movie>>
    ) => {
      return {
        ...state,
        wantedMovieList: updateOrderIdState(
          action,
          state.wantedMovieList,
          "radarrId"
        ),
      };
    },
    [MOVIES_UPDATE_HISTORY_LIST]: (
      state,
      action: AsyncAction<History.Movie[]>
    ) => {
      return {
        ...state,
        historyList: updateAsyncState(action, state.historyList.data),
      };
    },
    [MOVIES_UPDATE_LIST]: (
      state,
      action: AsyncAction<AsyncDataWrapper<Item.Movie>>
    ) => {
      return {
        ...state,
        movieList: updateOrderIdState(action, state.movieList, "radarrId"),
      };
    },
    [MOVIES_UPDATE_RANGE]: (
      state,
      action: AsyncAction<AsyncDataWrapper<Item.Movie>>
    ) => {
      return {
        ...state,
        movieList: updateOrderIdState(action, state.movieList, "radarrId"),
      };
    },
    [MOVIES_UPDATE_BLACKLIST]: (
      state,
      action: AsyncAction<Blacklist.Movie[]>
    ) => {
      return {
        ...state,
        blacklist: updateAsyncState(action, state.blacklist.data),
      };
    },
  },
  {
    movieList: { updating: true, data: { items: {}, order: [] } },
    wantedMovieList: { updating: true, data: { items: {}, order: [] } },
    historyList: { updating: true, data: [] },
    blacklist: { updating: true, data: [] },
  }
);

export default reducer;
