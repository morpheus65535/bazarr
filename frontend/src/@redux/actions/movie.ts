import { MoviesApi, HistoryApi } from "../../apis";
import {
  UPDATE_MOVIE_HISTORY_LIST,
  UPDATE_MOVIE_LIST,
  UPDATE_MOVIE_WANTED_LIST,
  UPDATE_MOVIE_INFO,
} from "../constants";
import { createAsyncAction, createAsyncAction1 } from "./creator";

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

export const updateMovieInfo = createAsyncAction1(
  UPDATE_MOVIE_INFO,
  (id: number) => MoviesApi.movies(id)
);
