import {
  SITE_NEED_AUTH,
  SITE_INITIALIZED,
  SITE_AUTH_SUCCESS,
} from "../constants";
import { createFillfulAction } from "./utils";
import { updateBadges } from "./badges";
import { updateLanguagesList } from "./system";
import { createAction } from "redux-actions";

export const bootstrap = createFillfulAction(
  () => [updateBadges(), updateLanguagesList()],
  (state) => {
    const { system } = state;
    if (
      !system.languages.updating &&
      !system.enabledLanguage.updating &&
      !system.languagesProfiles.updating
    ) {
      return siteInitialized();
    }
  }
);

const siteInitialized = createAction(SITE_INITIALIZED);

export const redirectToAuth = createAction(SITE_NEED_AUTH);

export const authSuccess = createAction(SITE_AUTH_SUCCESS);
