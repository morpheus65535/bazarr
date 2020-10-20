import { AsyncPayload } from "../types/actions";
import {
  UPDATE_LANGUAGES_LIST,
  UPDATE_SYSTEM_STATUS,
  UPDATE_SYSTEM_TASKS,
  EXEC_SYSTEM_TASK,
} from "../constants";
import { mapToAsyncState } from "./mapper";

import { handleActions, Action as RAction } from "redux-actions";

const reducer = handleActions<SystemState, any>(
  {
    [UPDATE_LANGUAGES_LIST]: {
      next(state, action) {
        return {
          ...state,
          languages: mapToAsyncState<Array<Language>>(action, []),
        };
      },
    },
    [UPDATE_SYSTEM_STATUS]: {
      next(state, action) {
        return {
          ...state,
          status: mapToAsyncState<SystemStatusResult>(
            action,
            state.status.items
          ),
        };
      },
    },
    [UPDATE_SYSTEM_TASKS]: {
      next(state, action) {
        return {
          ...state,
          tasks: mapToAsyncState<Array<SystemTaskResult>>(
            action,
            state.tasks.items
          ),
        };
      },
    },
    [EXEC_SYSTEM_TASK]: {
      next(state, action) {
        const { payload } = action as RAction<string>;

        let items = state.tasks.items.map((val) => {
          if (val.job_id == payload) {
            val.job_running = true;
          }
          return val;
        });
        return {
          ...state,
          tasks: {
            ...state.tasks,
            items,
          },
        };
      },
    },
  },
  {
    languages: { loading: false, items: [] },
    status: {
      loading: false,
      items: {
        bazarr_config_directory: "",
        bazarr_directory: "",
        bazarr_version: "",
        operating_system: "",
        python_version: "",
        radarr_version: "",
        sonarr_version: "",
      },
    },
    tasks: {
      loading: false,
      items: [],
    },
  }
);

export default reducer;
