import { MoviesApi, HistoryApi } from "../../apis";
import {
  UPDATE_MOVIE_HISTORY_LIST,
  UPDATE_MOVIE_LIST,
  UPDATE_MOVIE_WANTED_LIST,
} from "../constants";
import { createAsyncAction } from "./creator";

export const updateMovieList = createAsyncAction(UPDATE_MOVIE_LIST, () =>
  MoviesApi.movies()
);

export const updateWantedMovieList = createAsyncAction(
  UPDATE_MOVIE_WANTED_LIST,
  () => MoviesApi.wanted()
);

export const updateHistoryMovieList = createAsyncAction(
  UPDATE_MOVIE_HISTORY_LIST,
  () => HistoryApi.movies()
);
