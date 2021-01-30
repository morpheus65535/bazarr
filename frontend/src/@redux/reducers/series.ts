import { AsyncAction } from "../types";
import {
  UPDATE_SERIES_EPISODE_LIST,
  UPDATE_SERIES_LIST,
  UPDATE_SERIES_WANTED_LIST,
  UPDATE_SERIES_HISTORY_LIST,
  UPDATE_SERIES_INFO,
  UPDATE_SERIES_BLACKLIST,
} from "../constants";
import { mapToAsyncState, updateAsyncList } from "./mapper";

import { handleActions } from "redux-actions";

const reducer = handleActions<SeriesState, any>(
  {
    [UPDATE_SERIES_LIST]: {
      next(state, action: AsyncAction<Series[]>) {
        return {
          ...state,
          seriesList: mapToAsyncState(action, state.seriesList.items),
        };
      },
    },
    [UPDATE_SERIES_WANTED_LIST]: {
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
    [UPDATE_SERIES_EPISODE_LIST]: {
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
    [UPDATE_SERIES_HISTORY_LIST]: {
      next(state, action: AsyncAction<SeriesHistory[]>) {
        return {
          ...state,
          historyList: mapToAsyncState(action, state.historyList.items),
        };
      },
    },
    [UPDATE_SERIES_INFO]: {
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
    [UPDATE_SERIES_BLACKLIST]: {
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
