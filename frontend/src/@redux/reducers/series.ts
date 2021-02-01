import { handleActions } from "redux-actions";
import {
  SERIES_UPDATE_BLACKLIST,
  SERIES_UPDATE_EPISODE_LIST,
  SERIES_UPDATE_HISTORY_LIST,
  SERIES_UPDATE_INFO,
  SERIES_UPDATE_LIST,
  SERIES_UPDATE_WANTED_LIST,
} from "../constants";
import { AsyncAction } from "../types";
import { mapToAsyncState, updateAsyncList } from "./mapper";

const reducer = handleActions<SeriesState, any>(
  {
    [SERIES_UPDATE_LIST]: {
      next(state, action: AsyncAction<Series[]>) {
        return {
          ...state,
          seriesList: mapToAsyncState(action, state.seriesList.items),
        };
      },
    },
    [SERIES_UPDATE_WANTED_LIST]: {
      next(state, action: AsyncAction<WantedEpisode[]>) {
        return {
          ...state,
          wantedSeriesList: mapToAsyncState(
            action,
            state.wantedSeriesList.items
          ),
        };
      },
    },
    [SERIES_UPDATE_EPISODE_LIST]: {
      next(state, action: AsyncAction<Episode[]>) {
        const { updating, error, items } = mapToAsyncState(action, []);

        if (items.length > 0) {
          const id = items[0].sonarrSeriesId;
          const list = state.episodeList.items;
          list.set(id, items);
          return {
            ...state,
            episodeList: {
              updating,
              error,
              items: list,
            },
          };
        } else {
          return {
            ...state,
            episodeList: {
              ...state.episodeList,
              updating,
              error,
            },
          };
        }
      },
    },
    [SERIES_UPDATE_HISTORY_LIST]: {
      next(state, action: AsyncAction<SeriesHistory[]>) {
        return {
          ...state,
          historyList: mapToAsyncState(action, state.historyList.items),
        };
      },
    },
    [SERIES_UPDATE_INFO]: {
      next(state, action: AsyncAction<Series[]>) {
        return {
          ...state,
          seriesList: updateAsyncList(
            action,
            state.seriesList,
            "sonarrSeriesId"
          ),
        };
      },
    },
    [SERIES_UPDATE_BLACKLIST]: {
      next(state, action: AsyncAction<SeriesBlacklist[]>) {
        return {
          ...state,
          blacklist: mapToAsyncState(action, state.blacklist.items),
        };
      },
    },
  },
  {
    seriesList: { updating: true, items: [] },
    wantedSeriesList: { updating: true, items: [] },
    episodeList: { updating: true, items: new Map() },
    historyList: { updating: true, items: [] },
    blacklist: { updating: true, items: [] },
  }
);

export default reducer;
