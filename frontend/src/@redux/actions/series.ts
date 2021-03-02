import { EpisodesApi, SeriesApi } from "../../apis";
import {
  SERIES_UPDATE_BLACKLIST,
  SERIES_UPDATE_EPISODE_LIST,
  SERIES_UPDATE_HISTORY_LIST,
  SERIES_UPDATE_INFO,
  SERIES_UPDATE_LIST,
  SERIES_UPDATE_WANTED_LIST,
} from "../constants";
import { badgeUpdateSeries, updateBadges } from "./badges";
import { createAsyncAction, createCombineAction } from "./utils";

export const seriesUpdateList = createAsyncAction(SERIES_UPDATE_LIST, () =>
  SeriesApi.series()
);

export const seriesUpdateWantedList = createAsyncAction(
  SERIES_UPDATE_WANTED_LIST,
  () => EpisodesApi.wanted()
);

export const seriesUpdateWantedAll = createCombineAction(() => [
  seriesUpdateWantedList(),
  badgeUpdateSeries(),
]);

export const episodeUpdateInfo = createAsyncAction(
  SERIES_UPDATE_EPISODE_LIST,
  (id: number) => EpisodesApi.all(id)
);

export const seriesUpdateHistoryList = createAsyncAction(
  SERIES_UPDATE_HISTORY_LIST,
  () => EpisodesApi.history()
);

export const seriesUpdateInfo = createAsyncAction(
  SERIES_UPDATE_INFO,
  (id?: number) => SeriesApi.series(id)
);

export const seriesUpdateInfoAll = createCombineAction((id?: number) => {
  const actions = [seriesUpdateInfo(id), updateBadges()];
  if (id !== undefined) {
    actions.push(episodeUpdateInfo(id));
  }
  return actions;
});

export const seriesUpdateBlacklist = createAsyncAction(
  SERIES_UPDATE_BLACKLIST,
  () => EpisodesApi.blacklist()
);
