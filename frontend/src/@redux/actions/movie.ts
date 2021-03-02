import { MoviesApi } from "../../apis";
import {
  MOVIES_UPDATE_BLACKLIST,
  MOVIES_UPDATE_HISTORY_LIST,
  MOVIES_UPDATE_INFO,
} from "../constants";
import { badgeUpdateMovies } from "./badges";
import { createAsyncAction, createCombineAction } from "./utils";

export const movieUpdateHistoryList = createAsyncAction(
  MOVIES_UPDATE_HISTORY_LIST,
  () => MoviesApi.history()
);

const movieUpdateInfo = createAsyncAction(MOVIES_UPDATE_INFO, (id?: number) =>
  MoviesApi.movies(id)
);

export const movieUpdateInfoAll = createCombineAction((id?: number) => {
  return [movieUpdateInfo(id), badgeUpdateMovies()];
});

export const movieUpdateBlacklist = createAsyncAction(
  MOVIES_UPDATE_BLACKLIST,
  () => MoviesApi.blacklist()
);
