import { UPDATE_BADGE_ALL } from "../constants";

import { handleActions } from "redux-actions";

const reducer = handleActions<BadgeState, number[]>(
  {
    [UPDATE_BADGE_ALL]: {
      next(state, action) {
        return {
          ...state,
          episodes: action.payload[0],
          movies: action.payload[1],
          providers: action.payload[2],
        };
      },
    },
  },
  {
    movies: 0,
    episodes: 0,
    providers: 0,
  }
);

export default reducer;
