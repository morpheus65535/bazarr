import { AsyncAction } from "../types";
import {
  UPDATE_SERIES_EPISODE_LIST,
  UPDATE_SERIES_LIST,
  UPDATE_SERIES_WANTED_LIST,
  UPDATE_SERIES_HISTORY_LIST,
  UPDATE_SERIES_INFO,
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
        const { updating, lastResult, items } = mapToAsyncState(action, []);

        if (items.length > 0) {
          const id = items[0].sonarrSeriesId;
          const list = state.episodeList.items;
          list.set(id, items);
          return {
            ...state,
            episodeList: {
              updating,
              lastResult,
              items: list,
            },
          };
        } else {
          return {
            ...state,
            episodeList: {
              ...state.episodeList,
              updating,
              lastResult,
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
          seriesList: updateAsyncList(action, state.seriesList, "sonarrSeriesId")
        };
      }
    }
  },
  {
    seriesList: { updating: false, items: [] },
    wantedSeriesList: { updating: false, items: [] },
    episodeList: { updating: false, items: new Map() },
    historyList: { updating: false, items: [] },
  }
);

export default reducer;
