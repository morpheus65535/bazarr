import { Action, handleActions } from "redux-actions";
import {
  MOVIES_DELETE_ITEMS,
  MOVIES_DELETE_WANTED_ITEMS,
  MOVIES_UPDATE_BLACKLIST,
  MOVIES_UPDATE_HISTORY_LIST,
  MOVIES_UPDATE_LIST,
  MOVIES_UPDATE_WANTED_LIST,
} from "../constants";
import { AsyncAction } from "../types";
import { defaultAOS } from "../utils";
import {
  deleteOrderListItemBy,
  updateAsyncState,
  updateOrderIdState,
} from "../utils/mapper";

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
    [MOVIES_DELETE_WANTED_ITEMS]: (state, action: Action<number[]>) => {
      return {
        ...state,
        wantedMovieList: deleteOrderListItemBy(action, state.wantedMovieList),
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
    [MOVIES_DELETE_ITEMS]: (state, action: Action<number[]>) => {
      return {
        ...state,
        movieList: deleteOrderListItemBy(action, state.movieList),
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
    movieList: defaultAOS(),
    wantedMovieList: defaultAOS(),
    historyList: { updating: true, data: [] },
    blacklist: { updating: true, data: [] },
  }
);

export default reducer;
