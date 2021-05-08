import { MoviesApi } from "../../apis";
import {
  MOVIES_DELETE_ITEMS,
  MOVIES_DELETE_WANTED_ITEMS,
  MOVIES_UPDATE_BLACKLIST,
  MOVIES_UPDATE_HISTORY_LIST,
  MOVIES_UPDATE_LIST,
  MOVIES_UPDATE_WANTED_LIST,
} from "../constants";
import { createAsyncAction, createDeleteAction } from "./factory";

export const movieUpdateList = createAsyncAction(
  MOVIES_UPDATE_LIST,
  (id?: number[]) => MoviesApi.movies(id)
);

export const movieDeleteItems = createDeleteAction(MOVIES_DELETE_ITEMS);

export const movieUpdateWantedList = createAsyncAction(
  MOVIES_UPDATE_WANTED_LIST,
  (radarrid: number[]) => MoviesApi.wantedBy(radarrid)
);

export const movieDeleteWantedItems = createDeleteAction(
  MOVIES_DELETE_WANTED_ITEMS
);

export const movieUpdateWantedByRange = createAsyncAction(
  MOVIES_UPDATE_WANTED_LIST,
  (start: number, length: number) => MoviesApi.wanted(start, length)
);

export const movieUpdateHistoryList = createAsyncAction(
  MOVIES_UPDATE_HISTORY_LIST,
  () => MoviesApi.history()
);

export const movieUpdateByRange = createAsyncAction(
  MOVIES_UPDATE_LIST,
  (start: number, length: number) => MoviesApi.moviesBy(start, length)
);

export const movieUpdateBlacklist = createAsyncAction(
  MOVIES_UPDATE_BLACKLIST,
  () => MoviesApi.blacklist()
);
