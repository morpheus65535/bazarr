import apis from "../../apis"
import { UPDATE_MOVIE_LIST } from "../constants"
import { createAsyncAction } from "./creator"

export const updateMovieList = createAsyncAction(UPDATE_MOVIE_LIST, () =>
    apis.movie.movies()
);