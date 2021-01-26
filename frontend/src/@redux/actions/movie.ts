import { MoviesApi, HistoryApi } from "../../apis";
import {
  UPDATE_MOVIE_HISTORY_LIST,
  UPDATE_MOVIE_LIST,
  UPDATE_MOVIE_WANTED_LIST,
  UPDATE_MOVIE_INFO,
  UPDATE_MOVIES_BLACKLIST,
} from "../constants";
import { updateBadgeMovies, updateBadges } from "./badges";
import { createAsyncAction, createCombineAction } from "./utils";

export const updateMovieList = createAsyncAction(UPDATE_MOVIE_LIST, () =>
  MoviesApi.movies()
);

export const updateWantedMovieList = createAsyncAction(
  UPDATE_MOVIE_WANTED_LIST,
  () => MoviesApi.wanted()
);

export const updateWantedMovies = createCombineAction(() => [
  updateWantedMovieList(),
  updateBadgeMovies(),
]);

export const updateHistoryMovieList = createAsyncAction(
  UPDATE_MOVIE_HISTORY_LIST,
  () => HistoryApi.movies()
);

export const updateMovie = createAsyncAction(UPDATE_MOVIE_INFO, (id: number) =>
  MoviesApi.movies(id)
);

export const updateMovieInfo = createCombineAction((id: number) => {
  return [updateMovie(id), updateBadges()];
});

export const updateMovieBlacklist = createAsyncAction(
  UPDATE_MOVIES_BLACKLIST,
  () => MoviesApi.blacklist()
);
