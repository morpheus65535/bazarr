import { createAction } from "redux-actions";
import { BadgesApi } from "../../apis";
import {
  SITE_BADGE_UPDATE,
  SITE_INITIALIZED,
  SITE_INITIALIZE_FAILED,
  SITE_NEED_AUTH,
  SITE_NOTIFICATIONS_ADD,
  SITE_NOTIFICATIONS_REMOVE,
  SITE_OFFLINE_UPDATE,
  SITE_SIDEBAR_UPDATE,
} from "../constants";
import { createAsyncAction, createCallbackAction } from "./factory";
import { systemUpdateLanguagesAll, systemUpdateSettings } from "./system";

export const bootstrap = createCallbackAction(
  () => [systemUpdateLanguagesAll(), systemUpdateSettings(), badgeUpdateAll()],
  () => siteInitialized(),
  () => siteInitializationFailed()
);

// TODO: Override error messages
export const siteInitializationFailed = createAction(SITE_INITIALIZE_FAILED);

const siteInitialized = createAction(SITE_INITIALIZED);

export const siteRedirectToAuth = createAction(SITE_NEED_AUTH);

export const badgeUpdateAll = createAsyncAction(SITE_BADGE_UPDATE, () =>
  BadgesApi.all()
);

export const siteAddNotifications = createAction(
  SITE_NOTIFICATIONS_ADD,
  (err: ReduxStore.Notification[]) => err
);

export const siteRemoveNotifications = createAction(
  SITE_NOTIFICATIONS_REMOVE,
  (id: string) => id
);

export const siteChangeSidebar = createAction(
  SITE_SIDEBAR_UPDATE,
  (id: string) => id
);

export const siteUpdateOffline = createAction(
  SITE_OFFLINE_UPDATE,
  (state: boolean) => state
);
