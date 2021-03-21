import { EpisodesApi, SeriesApi } from "../../apis";
import {
  SERIES_UPDATE_BLACKLIST,
  SERIES_UPDATE_EPISODE_LIST,
  SERIES_UPDATE_HISTORY_LIST,
  SERIES_UPDATE_INFO,
  SERIES_UPDATE_RANGE,
  SERIES_UPDATE_WANTED_LIST,
  SERIES_UPDATE_WANTED_RANGE,
} from "../constants";
import {
  createAsyncAction,
  createAsyncCombineAction,
  createCombineAction,
} from "./factory";
import { badgeUpdateAll } from "./site";

const seriesUpdateWantedList = createAsyncAction(
  SERIES_UPDATE_WANTED_LIST,
  (episodeid?: number) => EpisodesApi.wantedBy(episodeid)
);

const seriesUpdateBy = createAsyncAction(SERIES_UPDATE_INFO, (id?: number[]) =>
  SeriesApi.series(id)
);

const episodeUpdateBy = createAsyncAction(
  SERIES_UPDATE_EPISODE_LIST,
  (seriesid: number) => EpisodesApi.bySeriesId(seriesid)
);

export const seriesUpdateByRange = createAsyncAction(
  SERIES_UPDATE_RANGE,
  (start: number, length: number) => SeriesApi.seriesBy(start, length)
);

export const seriesUpdateWantedByRange = createAsyncAction(
  SERIES_UPDATE_WANTED_RANGE,
  (start: number, length: number) => EpisodesApi.wanted(start, length)
);

export const seriesUpdateWantedBy = createCombineAction(
  (episodeid?: number) => [seriesUpdateWantedList(episodeid), badgeUpdateAll()]
);

export const episodeUpdateBySeriesId = createCombineAction(
  (seriesid: number) => [episodeUpdateBy(seriesid), badgeUpdateAll()]
);

export const seriesUpdateHistoryList = createAsyncAction(
  SERIES_UPDATE_HISTORY_LIST,
  () => EpisodesApi.history()
);

export const seriesUpdateInfoAll = createAsyncCombineAction(
  (seriesid?: number[]) => [seriesUpdateBy(seriesid), badgeUpdateAll()]
);

export const seriesUpdateBlacklist = createAsyncAction(
  SERIES_UPDATE_BLACKLIST,
  () => EpisodesApi.blacklist()
);
