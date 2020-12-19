import {
  UPDATE_LANGUAGES_LIST,
  UPDATE_SYSTEM_STATUS,
  UPDATE_SYSTEM_TASKS,
  UPDATE_SYSTEM_PROVIDERS,
  UPDATE_SYSTEM_LOGS,
  EXEC_SYSTEM_TASK,
} from "../constants";

import apis from "../../apis";
import { createAsyncAction } from "./creator";
import { Action } from "redux-actions";

export const updateLanguagesList = createAsyncAction(
  UPDATE_LANGUAGES_LIST,
  (enabled: boolean = false) => apis.system.languages(enabled)
);

export const UpdateSystemStatus = createAsyncAction(UPDATE_SYSTEM_STATUS, () =>
  apis.system.status()
);

export const UpdateSystemTasks = createAsyncAction(UPDATE_SYSTEM_TASKS, () =>
  apis.system.getTasks()
);

export const UpdateSystemProviders = createAsyncAction(
  UPDATE_SYSTEM_PROVIDERS,
  () => apis.system.providers()
);

export const UpdateSystemLogs = createAsyncAction(
  UPDATE_SYSTEM_LOGS,
  () => apis.system.logs()
)

export const ExecSystemTask = (id: string): Action<string> => {
  apis.system.execTasks(id);
  return {
    type: EXEC_SYSTEM_TASK,
    payload: id,
  };
};
