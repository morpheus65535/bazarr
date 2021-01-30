import {
  SYSTEM_UPDATE_LANGUAGES_LIST,
  SYSTEM_UPDATE_ENABLED_LANGUAGES_LIST,
  SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST,
  SYSTEM_UPDATE_SYSTEM_STATUS,
  SYSTEM_UPDATE_SYSTEM_TASKS,
  SYSTEM_UPDATE_SYSTEM_LOGS,
  SYSTEM_UPDATE_SYSTEM_SETTINGS,
} from "../constants";

import { SystemApi } from "../../apis";
import { createAsyncAction, createCombineAction } from "./utils";

export const systemUpdateLanguagesAll = createCombineAction(() => [
  systemUpdateLanguages(),
  systemUpdateEnabledLanguages(),
  systemUpdateLanguagesProfiles(),
]);

export const systemUpdateLanguages = createAsyncAction(
  SYSTEM_UPDATE_LANGUAGES_LIST,
  () => SystemApi.languages(false)
);

export const systemUpdateEnabledLanguages = createAsyncAction(
  SYSTEM_UPDATE_ENABLED_LANGUAGES_LIST,
  () => SystemApi.languages(true)
);

export const systemUpdateLanguagesProfiles = createAsyncAction(
  SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST,
  () => SystemApi.languagesProfileList()
);

export const systemUpdateSystemStatus = createAsyncAction(
  SYSTEM_UPDATE_SYSTEM_STATUS,
  () => SystemApi.status()
);

export const systemUpdateSystemTasks = createAsyncAction(
  SYSTEM_UPDATE_SYSTEM_TASKS,
  () => SystemApi.getTasks()
);

export const systemUpdateSystemLogs = createAsyncAction(
  SYSTEM_UPDATE_SYSTEM_LOGS,
  () => SystemApi.logs()
);

export const systemUpdateSystemSettings = createAsyncAction(
  SYSTEM_UPDATE_SYSTEM_SETTINGS,
  () => SystemApi.settings()
);

export const systemUpdateSettingsAll = createCombineAction(() => [
  systemUpdateSystemSettings(),
  systemUpdateLanguagesProfiles(),
  systemUpdateEnabledLanguages(),
]);
