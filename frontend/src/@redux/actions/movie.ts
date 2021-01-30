import { MoviesApi, HistoryApi } from "../../apis";
import {
  MOVIES_UPDATE_HISTORY_LIST,
  MOVIES_UPDATE_LIST,
  MOVIES_UPDATE_WANTED_LIST,
  MOVIES_UPDATE_INFO,
  MOVIES_UPDATE_BLACKLIST,
} from "../constants";
import { badgeUpdateMovies, updateBadges } from "./badges";
import { createAsyncAction, createCombineAction } from "./utils";

export const movieUpdateList = createAsyncAction(MOVIES_UPDATE_LIST, () =>
  MoviesApi.movies()
);

export const movieUpdateWantedList = createAsyncAction(
  MOVIES_UPDATE_WANTED_LIST,
  () => MoviesApi.wanted()
);

export const movieUpdateWantedAll = createCombineAction(() => [
  movieUpdateWantedList(),
  badgeUpdateMovies(),
]);

export const movieUpdateHistoryList = createAsyncAction(
  MOVIES_UPDATE_HISTORY_LIST,
  () => HistoryApi.movies()
);

export const movieUpdateInfo = createAsyncAction(
  MOVIES_UPDATE_INFO,
  (id: number) => MoviesApi.movies(id)
);

export const movieUpdateInfoAll = createCombineAction((id: number) => {
  return [movieUpdateInfo(id), updateBadges()];
});

export const movieUpdateBlacklist = createAsyncAction(
  MOVIES_UPDATE_BLACKLIST,
  () => MoviesApi.blacklist()
);
