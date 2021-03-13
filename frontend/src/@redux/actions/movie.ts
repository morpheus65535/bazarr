import { MoviesApi } from "../../apis";
import {
  MOVIES_UPDATE_BLACKLIST,
  MOVIES_UPDATE_HISTORY_LIST,
  MOVIES_UPDATE_INFO,
  MOVIES_UPDATE_RANGE,
} from "../constants";
import { createAsyncAction, createCombineAction } from "./factory";
import { badgeUpdateAll } from "./site";

export const movieUpdateHistoryList = createAsyncAction(
  MOVIES_UPDATE_HISTORY_LIST,
  () => MoviesApi.history()
);

const movieUpdateInfo = createAsyncAction(MOVIES_UPDATE_INFO, (id?: number) =>
  MoviesApi.movies(id)
);

export const movieUpdateByRange = createAsyncAction(
  MOVIES_UPDATE_RANGE,
  (start: number, length: number) => MoviesApi.moviesBy(start, length)
);

export const movieUpdateInfoAll = createCombineAction((id?: number) => {
  return [movieUpdateInfo(id), badgeUpdateAll()];
});

export const movieUpdateBlacklist = createAsyncAction(
  MOVIES_UPDATE_BLACKLIST,
  () => MoviesApi.blacklist()
);
