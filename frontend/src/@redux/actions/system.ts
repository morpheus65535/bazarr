import {
  UPDATE_LANGUAGES_LIST,
  UPDATE_SYSTEM_STATUS,
  UPDATE_SYSTEM_TASKS,
  UPDATE_SYSTEM_PROVIDERS,
  UPDATE_SYSTEM_LOGS,
  EXEC_SYSTEM_TASK,
} from "../constants";

import { SystemApi } from "../../apis";
import { createAsyncAction } from "./creator";
import { Action } from "redux-actions";

export const updateLanguagesList = createAsyncAction(
  UPDATE_LANGUAGES_LIST,
  (enabled: boolean = false) => SystemApi.languages(enabled)
);

export const UpdateSystemStatus = createAsyncAction(UPDATE_SYSTEM_STATUS, () =>
  SystemApi.status()
);

export const UpdateSystemTasks = createAsyncAction(UPDATE_SYSTEM_TASKS, () =>
  SystemApi.getTasks()
);

export const UpdateSystemProviders = createAsyncAction(
  UPDATE_SYSTEM_PROVIDERS,
  () => SystemApi.providers()
);

export const UpdateSystemLogs = createAsyncAction(
  UPDATE_SYSTEM_LOGS,
  () => SystemApi.logs()
)

export const ExecSystemTask = (id: string): Action<string> => {
  SystemApi.execTasks(id);
  return {
    type: EXEC_SYSTEM_TASK,
    payload: id,
  };
};
