import apis from "../../apis";
import {
  UPDATE_MOVIE_HISTORY_LIST,
  UPDATE_MOVIE_LIST,
  UPDATE_MOVIE_WANTED_LIST,
} from "../constants";
import { createAsyncAction } from "./creator";

export const updateMovieList = createAsyncAction(UPDATE_MOVIE_LIST, () =>
  apis.movie.movies()
);

export const updateWantedMovieList = createAsyncAction(
  UPDATE_MOVIE_WANTED_LIST,
  () => apis.movie.wanted()
);

export const updateHistoryMovieList = createAsyncAction(
  UPDATE_MOVIE_HISTORY_LIST,
  () => apis.history.movies()
);
