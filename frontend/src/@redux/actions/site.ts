import { createAction } from "redux-actions";
import {
  SITE_AUTH_SUCCESS,
  SITE_INITIALIZED,
  SITE_NEED_AUTH,
  SITE_SAVE_LOCALSTORAGE,
} from "../constants";
import { createCallbackAction } from "./factory";
import { systemUpdateLanguagesAll, systemUpdateSettings } from "./system";

export const bootstrap = createCallbackAction(
  () => [systemUpdateLanguagesAll(), systemUpdateSettings()],
  () => siteInitialized()
);

const siteInitialized = createAction(SITE_INITIALIZED);

export const siteRedirectToAuth = createAction(SITE_NEED_AUTH);

export const siteAuthSuccess = createAction(SITE_AUTH_SUCCESS);

export const siteSaveLocalstorage = createAction(
  SITE_SAVE_LOCALSTORAGE,
  (settings: LooseObject) => settings
);
