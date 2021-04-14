import { ProvidersApi, SystemApi } from "../../apis";
import {
  SYSTEM_UPDATE_LANGUAGES_LIST,
  SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST,
  SYSTEM_UPDATE_LOGS,
  SYSTEM_UPDATE_PROVIDERS,
  SYSTEM_UPDATE_RELEASES,
  SYSTEM_UPDATE_SETTINGS,
  SYSTEM_UPDATE_STATUS,
  SYSTEM_UPDATE_TASKS,
} from "../constants";
import { createAsyncAction, createAsyncCombineAction } from "./factory";

export const systemUpdateLanguagesAll = createAsyncCombineAction(() => [
  systemUpdateLanguages(),
  systemUpdateLanguagesProfiles(),
]);

export const systemUpdateLanguages = createAsyncAction(
  SYSTEM_UPDATE_LANGUAGES_LIST,
  () => SystemApi.languages()
);

export const systemUpdateLanguagesProfiles = createAsyncAction(
  SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST,
  () => SystemApi.languagesProfileList()
);

export const systemUpdateStatus = createAsyncAction(SYSTEM_UPDATE_STATUS, () =>
  SystemApi.status()
);

export const systemUpdateTasks = createAsyncAction(SYSTEM_UPDATE_TASKS, () =>
  SystemApi.getTasks()
);

export const systemUpdateLogs = createAsyncAction(SYSTEM_UPDATE_LOGS, () =>
  SystemApi.logs()
);

export const systemUpdateReleases = createAsyncAction(
  SYSTEM_UPDATE_RELEASES,
  () => SystemApi.releases()
);

export const systemUpdateSettings = createAsyncAction(
  SYSTEM_UPDATE_SETTINGS,
  () => SystemApi.settings()
);

export const providerUpdateList = createAsyncAction(
  SYSTEM_UPDATE_PROVIDERS,
  () => ProvidersApi.providers()
);

export const systemUpdateSettingsAll = createAsyncCombineAction(() => [
  systemUpdateSettings(),
  systemUpdateLanguagesAll(),
]);
