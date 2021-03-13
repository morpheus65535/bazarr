import { handleActions } from "redux-actions";
import {
  SERIES_UPDATE_BLACKLIST,
  SERIES_UPDATE_EPISODE_LIST,
  SERIES_UPDATE_HISTORY_LIST,
  SERIES_UPDATE_INFO,
  SERIES_UPDATE_WANTED_LIST,
} from "../constants";
import { AsyncAction } from "../types";
import { mapToAsyncState, updateAsyncDataList } from "./mapper";

const reducer = handleActions<ReduxStore.Series, any>(
  {
    [SERIES_UPDATE_WANTED_LIST]: (
      state,
      action: AsyncAction<Wanted.Episode[]>
    ) => {
      return {
        ...state,
        wantedSeriesList: mapToAsyncState(action, state.wantedSeriesList.items),
      };
    },
    [SERIES_UPDATE_EPISODE_LIST]: (
      state,
      action: AsyncAction<Item.Episode[]>
    ) => {
      const { updating, error, items } = mapToAsyncState(action, []);

      const stateItems = { ...state.episodeList.items };

      if (items.length > 0) {
        const id = items[0].sonarrSeriesId;
        stateItems[id] = items;
      }

      return {
        ...state,
        episodeList: {
          updating,
          error,
          items: stateItems,
        },
      };
    },
    [SERIES_UPDATE_HISTORY_LIST]: (
      state,
      action: AsyncAction<History.Episode[]>
    ) => {
      return {
        ...state,
        historyList: mapToAsyncState(action, state.historyList.items),
      };
    },
    [SERIES_UPDATE_INFO]: (
      state,
      action: AsyncAction<AsyncDataWrapper<Item.Series>>
    ) => {
      return {
        ...state,
        seriesList: updateAsyncDataList(
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
        blacklist: mapToAsyncState(action, state.blacklist.items),
      };
    },
  },
  {
    seriesList: { updating: true, items: [] },
    wantedSeriesList: { updating: true, items: [] },
    episodeList: { updating: true, items: {} },
    historyList: { updating: true, items: [] },
    blacklist: { updating: true, items: [] },
  }
);

export default reducer;
