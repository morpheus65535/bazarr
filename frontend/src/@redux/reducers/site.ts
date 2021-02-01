import { handleActions } from "redux-actions";
import {
  SITE_AUTH_SUCCESS,
  SITE_INITIALIZED,
  SITE_NEED_AUTH,
} from "../constants";

const reducer = handleActions<SiteState, number>(
  {
    [SITE_NEED_AUTH]: (state) => ({
      ...state,
      auth: false,
    }),
    [SITE_AUTH_SUCCESS]: (state) => ({
      ...state,
      auth: true,
    }),
    [SITE_INITIALIZED]: (state) => ({
      ...state,
      initialized: true,
    }),
  },
  {
    initialized: false,
    auth: true,
  }
);

export default reducer;
