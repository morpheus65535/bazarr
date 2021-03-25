import { handleActions } from "redux-actions";
import {
  SERIES_UPDATE_BLACKLIST,
  SERIES_UPDATE_EPISODE_LIST,
  SERIES_UPDATE_HISTORY_LIST,
  SERIES_UPDATE_INFO,
  SERIES_UPDATE_RANGE,
  SERIES_UPDATE_WANTED_LIST,
  SERIES_UPDATE_WANTED_RANGE,
} from "../constants";
import { AsyncAction } from "../types";
import { updateAsyncState, updateOrderIdState } from "./mapper";

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
    [SERIES_UPDATE_WANTED_RANGE]: (
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
    [SERIES_UPDATE_EPISODE_LIST]: (
      state,
      action: AsyncAction<Item.Episode[]>
    ) => {
      const { updating, error, data: items } = updateAsyncState(action, []);

      const stateItems = { ...state.episodeList.data };

      if (items.length > 0) {
        const id = items[0].sonarrSeriesId;
        stateItems[id] = items;
      }

      return {
        ...state,
        episodeList: {
          updating,
          error,
          data: stateItems,
        },
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
    [SERIES_UPDATE_INFO]: (
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
    [SERIES_UPDATE_RANGE]: (
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
    seriesList: { updating: true, data: { items: {}, order: [] } },
    wantedEpisodesList: { updating: true, data: { items: {}, order: [] } },
    episodeList: { updating: true, data: {} },
    historyList: { updating: true, data: [] },
    blacklist: { updating: true, data: [] },
  }
);

export default reducer;
