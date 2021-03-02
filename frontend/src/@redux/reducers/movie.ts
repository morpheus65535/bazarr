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

const reducer = handleActions<ReduxStore.Movie, any>(
  {
    [MOVIES_UPDATE_LIST]: (state, action: AsyncAction<Item.Movie[]>) => {
      return {
        ...state,
        movieList: mapToAsyncState(action, state.movieList.items),
      };
    },
    [MOVIES_UPDATE_WANTED_LIST]: (
      state,
      action: AsyncAction<Wanted.Movie[]>
    ) => {
      return {
        ...state,
        wantedMovieList: mapToAsyncState(action, state.wantedMovieList.items),
      };
    },
    [MOVIES_UPDATE_HISTORY_LIST]: (
      state,
      action: AsyncAction<History.Movie[]>
    ) => {
      return {
        ...state,
        historyList: mapToAsyncState(action, state.historyList.items),
      };
    },
    [MOVIES_UPDATE_INFO]: (state, action: AsyncAction<Item.Movie[]>) => {
      return {
        ...state,
        movieList: updateAsyncList(action, state.movieList, "radarrId"),
      };
    },
    [MOVIES_UPDATE_BLACKLIST]: (
      state,
      action: AsyncAction<Blacklist.Movie[]>
    ) => {
      return {
        ...state,
        blacklist: mapToAsyncState(action, state.blacklist.items),
      };
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
