import { createDeleteAction } from "../../@socketio/reducer";
import { EpisodesApi, SeriesApi } from "../../apis";
import {
  SERIES_DELETE_EPISODES,
  SERIES_DELETE_ITEMS,
  SERIES_DELETE_WANTED_ITEMS,
  SERIES_UPDATE_BLACKLIST,
  SERIES_UPDATE_EPISODE_LIST,
  SERIES_UPDATE_HISTORY_LIST,
  SERIES_UPDATE_LIST,
  SERIES_UPDATE_WANTED_LIST,
} from "../constants";
import { createAsyncAction } from "./factory";

export const seriesUpdateWantedList = createAsyncAction(
  SERIES_UPDATE_WANTED_LIST,
  (episodeid: number[]) => EpisodesApi.wantedBy(episodeid)
);

export const seriesDeleteWantedItems = createDeleteAction(
  SERIES_DELETE_WANTED_ITEMS
);

export const seriesUpdateWantedByRange = createAsyncAction(
  SERIES_UPDATE_WANTED_LIST,
  (start: number, length: number) => EpisodesApi.wanted(start, length)
);

export const seriesUpdateList = createAsyncAction(
  SERIES_UPDATE_LIST,
  (id?: number[]) => SeriesApi.series(id)
);

export const seriesDeleteItems = createDeleteAction(SERIES_DELETE_ITEMS);

export const episodeUpdateBy = createAsyncAction(
  SERIES_UPDATE_EPISODE_LIST,
  (seriesid: number[]) => EpisodesApi.bySeriesId(seriesid)
);

export const episodeDeleteItems = createDeleteAction(SERIES_DELETE_EPISODES);

export const episodeUpdateById = createAsyncAction(
  SERIES_UPDATE_EPISODE_LIST,
  (episodeid: number[]) => EpisodesApi.byEpisodeId(episodeid)
);

export const seriesUpdateByRange = createAsyncAction(
  SERIES_UPDATE_LIST,
  (start: number, length: number) => SeriesApi.seriesBy(start, length)
);

export const seriesUpdateHistoryList = createAsyncAction(
  SERIES_UPDATE_HISTORY_LIST,
  () => EpisodesApi.history()
);

export const seriesUpdateBlacklist = createAsyncAction(
  SERIES_UPDATE_BLACKLIST,
  () => EpisodesApi.blacklist()
);
