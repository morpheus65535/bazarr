import { AsyncAction } from "../types";
import {
  UPDATE_LANGUAGES_LIST,
  UPDATE_SYSTEM_STATUS,
  UPDATE_SYSTEM_TASKS,
  UPDATE_SYSTEM_PROVIDERS,
  UPDATE_SYSTEM_LOGS,
  EXEC_SYSTEM_TASK,
} from "../constants";
import { mapToAsyncState } from "./mapper";

import { handleActions, Action as RAction } from "redux-actions";
import Providers from "../../System/Providers";

const reducer = handleActions<SystemState, any>(
  {
    [UPDATE_LANGUAGES_LIST]: {
      next(state, action) {
        const payload = (action as AsyncAction<Array<ExtendLanguage>>).payload;
        let enabled = state.enabledLanguage;
        if (payload.loading === false) {
          enabled = (payload.item as ExtendLanguage[]).filter(
            (val) => Boolean(val.enabled) === true
          );
        }
        return {
          ...state,
          languages: mapToAsyncState<Array<ExtendLanguage>>(action, []),
          enabledLanguage: enabled,
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
    [UPDATE_SYSTEM_PROVIDERS]: {
      next(state, action) {
        return {
          ...state,
          providers: mapToAsyncState(action, state.providers.items),
        };
      },
    },
    [UPDATE_SYSTEM_LOGS]: {
      next(state, action) {
        return {
          ...state,
          logs: mapToAsyncState(action, state.logs.items),
        };
      },
    },
    [EXEC_SYSTEM_TASK]: {
      next(state, action) {
        const { payload } = action as RAction<string>;

        let items = state.tasks.items.map((val) => {
          if (val.job_id === payload) {
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
    languages: { updating: false, items: [] },
    enabledLanguage: [],
    status: {
      updating: false,
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
      updating: false,
      items: [],
    },
    providers: {
      updating: false,
      items: [],
    },
    logs: {
      updating: false,
      items: [],
    },
  }
);

export default reducer;
