import { createAction } from "redux-actions";
import {
  SITE_AUTH_SUCCESS,
  SITE_INITIALIZED,
  SITE_NEED_AUTH,
} from "../constants";
import { updateBadges } from "./badges";
import { systemUpdateLanguagesAll } from "./system";
import { createFillfulAction } from "./utils";

export const bootstrap = createFillfulAction(
  () => [updateBadges(), systemUpdateLanguagesAll()],
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

export const siteRedirectToAuth = createAction(SITE_NEED_AUTH);

export const siteAuthSuccess = createAction(SITE_AUTH_SUCCESS);
