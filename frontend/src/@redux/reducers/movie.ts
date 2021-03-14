import { handleActions } from "redux-actions";
import {
  MOVIES_UPDATE_BLACKLIST,
  MOVIES_UPDATE_HISTORY_LIST,
  MOVIES_UPDATE_INFO,
  MOVIES_UPDATE_RANGE,
} from "../constants";
import { AsyncAction } from "../types";
import { mapToAsyncState, updateAsyncDataList } from "./mapper";

const reducer = handleActions<ReduxStore.Movie, any>(
  {
    [MOVIES_UPDATE_HISTORY_LIST]: (
      state,
      action: AsyncAction<History.Movie[]>
    ) => {
      return {
        ...state,
        historyList: mapToAsyncState(action, state.historyList.items),
      };
    },
    [MOVIES_UPDATE_INFO]: (
      state,
      action: AsyncAction<AsyncDataWrapper<Item.Movie>>
    ) => {
      return {
        ...state,
        movieList: updateAsyncDataList(action, state.movieList, "radarrId"),
      };
    },
    [MOVIES_UPDATE_RANGE]: (
      state,
      action: AsyncAction<AsyncDataWrapper<Item.Movie>>
    ) => {
      return {
        ...state,
        movieList: updateAsyncDataList(action, state.movieList, "radarrId"),
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
    historyList: { updating: true, items: [] },
    blacklist: { updating: true, items: [] },
  }
);

export default reducer;
