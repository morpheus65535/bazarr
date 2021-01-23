import {
  UPDATE_BADGE_MOVIES,
  UPDATE_BADGE_PROVIDERS,
  UPDATE_BADGE_SERIES,
} from "../constants";

import { handleActions } from "redux-actions";

const reducer = handleActions<BadgeState, number>(
  {
    [UPDATE_BADGE_MOVIES]: {
      next(state, action) {
        return {
          ...state,
          movies: action.payload,
        };
      },
    },
    [UPDATE_BADGE_SERIES]: {
      next(state, action) {
        return {
          ...state,
          episodes: action.payload,
        };
      },
    },
    [UPDATE_BADGE_PROVIDERS]: {
      next(state, action) {
        return {
          ...state,
          providers: action.payload,
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
