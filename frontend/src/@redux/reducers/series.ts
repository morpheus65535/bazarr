import { Action, handleActions } from "redux-actions";
import {
  SERIES_DELETE_EPISODES,
  SERIES_DELETE_ITEMS,
  SERIES_DELETE_WANTED_ITEMS,
  SERIES_MARK_WANTED_LIST_DIRTY,
  SERIES_UPDATE_BLACKLIST,
  SERIES_UPDATE_EPISODE_LIST,
  SERIES_UPDATE_HISTORY_LIST,
  SERIES_UPDATE_LIST,
  SERIES_UPDATE_WANTED_LIST,
} from "../constants";
import { AsyncAction } from "../types";
import { defaultAOS } from "../utils";
import {
  deleteAsyncListItemBy,
  deleteOrderListItemBy,
  markOrderListDirty,
  updateAsyncList,
  updateAsyncState,
  updateOrderIdState,
} from "../utils/mapper";

const reducer = handleActions<ReduxStore.Series, any>(
  {
    [SERIES_UPDATE_WANTED_LIST]: (
      state,
      action: AsyncAction<AsyncDataWrapper<Wanted.Episode>>
    ) => {
      return {
        ...state,
        wantedEpisodesList: updateOrderIdState(
          action,
          state.wantedEpisodesList,
          "sonarrEpisodeId"
        ),
      };
    },
    [SERIES_DELETE_WANTED_ITEMS]: (state, action: Action<number[]>) => {
      return {
        ...state,
        wantedEpisodesList: deleteOrderListItemBy(
          action,
          state.wantedEpisodesList
        ),
      };
    },
    [SERIES_MARK_WANTED_LIST_DIRTY]: (state, action) => {
      return {
        ...state,
        wantedEpisodesList: markOrderListDirty(state.wantedEpisodesList),
      };
    },
    [SERIES_UPDATE_EPISODE_LIST]: (
      state,
      action: AsyncAction<Item.Episode[]>
    ) => {
      return {
        ...state,
        episodeList: updateAsyncList(
          action,
          state.episodeList,
          "sonarrEpisodeId"
        ),
      };
    },
    [SERIES_DELETE_EPISODES]: (state, action: Action<number[]>) => {
      return {
        ...state,
        episodeList: deleteAsyncListItemBy(
          action,
          state.episodeList,
          "sonarrEpisodeId"
        ),
      };
    },
    [SERIES_UPDATE_HISTORY_LIST]: (
      state,
      action: AsyncAction<History.Episode[]>
    ) => {
      return {
        ...state,
        historyList: updateAsyncState(action, state.historyList.data),
      };
    },
    [SERIES_UPDATE_LIST]: (
      state,
      action: AsyncAction<AsyncDataWrapper<Item.Series>>
    ) => {
      return {
        ...state,
        seriesList: updateOrderIdState(
          action,
          state.seriesList,
          "sonarrSeriesId"
        ),
      };
    },
    [SERIES_DELETE_ITEMS]: (state, action: Action<number[]>) => {
      return {
        ...state,
        seriesList: deleteOrderListItemBy(action, state.seriesList),
      };
    },
    [SERIES_UPDATE_BLACKLIST]: (
      state,
      action: AsyncAction<Blacklist.Episode[]>
    ) => {
      return {
        ...state,
        blacklist: updateAsyncState(action, state.blacklist.data),
      };
    },
  },
  {
    seriesList: defaultAOS(),
    wantedEpisodesList: defaultAOS(),
    episodeList: { updating: true, data: [] },
    historyList: { updating: true, data: [] },
    blacklist: { updating: true, data: [] },
  }
);

export default reducer;
