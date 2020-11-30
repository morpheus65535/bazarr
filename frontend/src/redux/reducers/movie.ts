import { AsyncAction } from "../types";
import { UPDATE_MOVIE_LIST } from "../constants";

import { mapToAsyncState } from "./mapper";

import { handleActions } from "redux-actions";

const reducer = handleActions<MovieState, any>(
  {
    [UPDATE_MOVIE_LIST]: {
      next(state, action: AsyncAction<Movie[]>) {
        return {
          ...state,
          movieList: mapToAsyncState(action, state.movieList.items),
        };
      },
    },
  },
  {
    movieList: { updating: false, items: [] },
  }
);

export default reducer;
