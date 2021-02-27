import { createAction } from "redux-actions";
import {
  SITE_AUTH_SUCCESS,
  SITE_INITIALIZED,
  SITE_NEED_AUTH,
  SITE_SAVE_LOCALSTORAGE,
} from "../constants";
import { updateBadges } from "./badges";
import { systemUpdateLanguagesAll } from "./system";
import { createFulfilAction } from "./utils";

export const bootstrap = createFulfilAction(
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

export const siteSaveLocalstorage = createAction(
  SITE_SAVE_LOCALSTORAGE,
  (settings: LooseObject) => settings
);
