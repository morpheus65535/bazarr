import { createAction } from "redux-actions";
import { BadgesApi } from "../../apis";
import {
  SITE_AUTH_SUCCESS,
  SITE_BADGE_UPDATE,
  SITE_INITIALIZED,
  SITE_NEED_AUTH,
  SITE_NOTIFICATIONS_ADD,
  SITE_NOTIFICATIONS_REMOVE,
  SITE_NOTIFICATIONS_REMOVE_BY_TIMESTAMP,
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
  SITE_NOTIFICATIONS_ADD,
  (err: ReduxStore.Notification) => err
);

export const siteRemoveError = createAction(
  SITE_NOTIFICATIONS_REMOVE,
  (id: string) => id
);

export const siteRemoveErrorByTimestamp = createAction(
  SITE_NOTIFICATIONS_REMOVE_BY_TIMESTAMP,
  (date: Date) => date
);

export const siteChangeSidebar = createAction(
  SITE_SIDEBAR_UPDATE,
  (id: string) => id
);
