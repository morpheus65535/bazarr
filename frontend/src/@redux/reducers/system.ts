import { Action, handleActions } from "redux-actions";
import {
  PROVIDER_UPDATE_LIST,
  SYSTEM_RUN_TASK,
  SYSTEM_UPDATE_LANGUAGES_LIST,
  SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST,
  SYSTEM_UPDATE_LOGS,
  SYSTEM_UPDATE_RELEASES,
  SYSTEM_UPDATE_SETTINGS,
  SYSTEM_UPDATE_STATUS,
  SYSTEM_UPDATE_TASKS,
} from "../constants";
import { mapToAsyncState } from "./mapper";

const reducer = handleActions<ReduxStore.System, any>(
  {
    [SYSTEM_UPDATE_LANGUAGES_LIST]: (state, action) => {
      const languages = mapToAsyncState<Array<ApiLanguage>>(action, []);
      const enabledLanguage: AsyncState<ApiLanguage[]> = {
        ...languages,
        data: languages.data.filter((v) => v.enabled),
      };
      const newState = {
        ...state,
        languages,
        enabledLanguage,
      };
      return newState;
    },
    [SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST]: (state, action) => {
      const newState = {
        ...state,
        languagesProfiles: mapToAsyncState<Array<Profile.Languages>>(
          action,
          []
        ),
      };
      return newState;
    },
    [SYSTEM_UPDATE_STATUS]: (state, action) => {
      return {
        ...state,
        status: mapToAsyncState<System.Status | undefined>(
          action,
          state.status.data
        ),
      };
    },
    [SYSTEM_UPDATE_TASKS]: (state, action) => {
      return {
        ...state,
        tasks: mapToAsyncState<Array<System.Task>>(action, state.tasks.data),
      };
    },
    [SYSTEM_RUN_TASK]: (state, action: Action<string>) => {
      const id = action.payload;
      const tasks = state.tasks;
      const newItems = [...tasks.data];

      const idx = newItems.findIndex((v) => v.job_id === id);

      if (idx !== -1) {
        newItems[idx].job_running = true;
      }

      return {
        ...state,
        tasks: {
          ...tasks,
          data: newItems,
        },
      };
    },
    [PROVIDER_UPDATE_LIST]: (state, action) => {
      return {
        ...state,
        providers: mapToAsyncState(action, state.providers.data),
      };
    },
    [SYSTEM_UPDATE_LOGS]: (state, action) => {
      return {
        ...state,
        logs: mapToAsyncState(action, state.logs.data),
      };
    },
    [SYSTEM_UPDATE_RELEASES]: (state, action) => {
      return {
        ...state,
        releases: mapToAsyncState(action, state.releases.data),
      };
    },
    [SYSTEM_UPDATE_SETTINGS]: (state, action) => {
      return {
        ...state,
        settings: mapToAsyncState(action, state.settings.data),
      };
    },
  },
  {
    languages: { updating: true, data: [] },
    enabledLanguage: { updating: true, data: [] },
    languagesProfiles: { updating: true, data: [] },
    status: {
      updating: true,
      data: undefined,
    },
    tasks: {
      updating: true,
      data: [],
    },
    providers: {
      updating: true,
      data: [],
    },
    logs: {
      updating: true,
      data: [],
    },
    releases: {
      updating: true,
      data: [],
    },
    settings: {
      updating: true,
      data: undefined,
    },
  }
);

export default reducer;
