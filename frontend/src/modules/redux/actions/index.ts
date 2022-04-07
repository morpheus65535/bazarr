import { createAction } from "@reduxjs/toolkit";

export const setSiteStatus = createAction<Site.Status>("site/status/update");

export const setUnauthenticated = createAction("site/unauthenticated");

export const setOfflineStatus = createAction<boolean>("site/offline/update");

export const setSidebar = createAction<boolean>("site/sidebar/update");
