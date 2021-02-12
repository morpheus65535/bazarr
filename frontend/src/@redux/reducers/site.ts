import { Action, handleActions } from "redux-actions";
import { uiPageSizeKey } from "../../@types/localStorage";
import {
  SITE_AUTH_SUCCESS,
  SITE_INITIALIZED,
  SITE_NEED_AUTH,
  SITE_SAVE_LOCALSTORAGE,
} from "../constants";

function updateLocalStorage(): Partial<SiteState> {
  return {
    pageSize: Number.parseInt(localStorage.getItem(uiPageSizeKey) ?? "50"),
  };
}

const reducer = handleActions<SiteState>(
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
    [SITE_SAVE_LOCALSTORAGE]: (state, action: Action<LooseObject>) => {
      const settings = action.payload;
      for (const key in settings) {
        const value = settings[key];
        localStorage.setItem(key, value);
      }
      return {
        ...state,
        ...updateLocalStorage(),
      };
    },
  },
  {
    initialized: false,
    auth: true,
    pageSize: 50,
    ...updateLocalStorage(),
  }
);

export default reducer;
