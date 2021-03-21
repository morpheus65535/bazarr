import { MoviesApi } from "../../apis";
import {
  MOVIES_UPDATE_BLACKLIST,
  MOVIES_UPDATE_HISTORY_LIST,
  MOVIES_UPDATE_INFO,
  MOVIES_UPDATE_LIST,
  MOVIES_UPDATE_RANGE,
  MOVIES_UPDATE_WANTED_LIST,
  MOVIES_UPDATE_WANTED_RANGE,
} from "../constants";
import {
  createAsyncAction,
  createAsyncCombineAction,
  createCombineAction,
} from "./factory";
import { badgeUpdateAll } from "./site";

export const movieUpdateList = createAsyncAction(MOVIES_UPDATE_LIST, () =>
  MoviesApi.movies()
);

const movieUpdateWantedList = createAsyncAction(
  MOVIES_UPDATE_WANTED_LIST,
  (radarrid?: number) => MoviesApi.wantedBy(radarrid)
);

export const movieUpdateWantedByRange = createAsyncAction(
  MOVIES_UPDATE_WANTED_RANGE,
  (start: number, length: number) => MoviesApi.wanted(start, length)
);

export const movieUpdateWantedBy = createCombineAction((radarrid?: number) => [
  movieUpdateWantedList(radarrid),
  badgeUpdateAll(),
]);

export const movieUpdateHistoryList = createAsyncAction(
  MOVIES_UPDATE_HISTORY_LIST,
  () => MoviesApi.history()
);

export const movieUpdateByRange = createAsyncAction(
  MOVIES_UPDATE_RANGE,
  (start: number, length: number) => MoviesApi.moviesBy(start, length)
);

const movieUpdateInfo = createAsyncAction(MOVIES_UPDATE_INFO, (id?: number[]) =>
  MoviesApi.movies(id)
);

export const movieUpdateInfoAll = createAsyncCombineAction((id?: number[]) => [
  movieUpdateInfo(id),
  badgeUpdateAll(),
]);

export const movieUpdateBlacklist = createAsyncAction(
  MOVIES_UPDATE_BLACKLIST,
  () => MoviesApi.blacklist()
);
