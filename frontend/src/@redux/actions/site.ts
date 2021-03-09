import { createAction } from "redux-actions";
import { BadgesApi } from "../../apis";
import {
  SITE_AUTH_SUCCESS,
  SITE_BADGE_UPDATE,
  SITE_ERROR_ADD,
  SITE_ERROR_REMOVE,
  SITE_ERROR_REMOVE_WITH_TIMESTAMP,
  SITE_INITIALIZED,
  SITE_NEED_AUTH,
  SITE_SAVE_LOCALSTORAGE,
  SITE_SIDEBAR_UPDATE,
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

export const badgeUpdateAll = createAction(SITE_BADGE_UPDATE, () =>
  BadgesApi.all()
);

export const siteSaveLocalstorage = createAction(
  SITE_SAVE_LOCALSTORAGE,
  (settings: LooseObject) => settings
);

export const siteAddError = createAction(
  SITE_ERROR_ADD,
  (err: ReduxStore.Error) => err
);

export const siteRemoveError = createAction(
  SITE_ERROR_REMOVE,
  (id: string) => id
);

export const siteRemoveErrorWithTimestamp = createAction(
  SITE_ERROR_REMOVE_WITH_TIMESTAMP,
  (date: Date) => date
);

export const siteChangeSidebar = createAction(
  SITE_SIDEBAR_UPDATE,
  (id: string) => id
);
