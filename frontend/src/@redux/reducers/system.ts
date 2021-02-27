import { Action, handleActions } from "redux-actions";
import {
  PROVIDER_UPDATE_LIST,
  SYSTEM_RUN_TASK,
  SYSTEM_UPDATE_ENABLED_LANGUAGES_LIST,
  SYSTEM_UPDATE_LANGUAGES_LIST,
  SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST,
  SYSTEM_UPDATE_LOGS,
  SYSTEM_UPDATE_RELEASES,
  SYSTEM_UPDATE_SETTINGS,
  SYSTEM_UPDATE_STATUS,
  SYSTEM_UPDATE_TASKS,
} from "../constants";
import { mapToAsyncState } from "./mapper";

const reducer = handleActions<SystemState, any>(
  {
    [SYSTEM_UPDATE_LANGUAGES_LIST]: (state, action) => {
      const newState = {
        ...state,
        languages: mapToAsyncState<Array<Language>>(action, []),
      };
      return newState;
    },
    [SYSTEM_UPDATE_ENABLED_LANGUAGES_LIST]: (state, action) => {
      const newState = {
        ...state,
        enabledLanguage: mapToAsyncState<Array<Language>>(action, []),
      };
      return newState;
    },
    [SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST]: (state, action) => {
      const newState = {
        ...state,
        languagesProfiles: mapToAsyncState<Array<LanguagesProfile>>(action, []),
      };
      return newState;
    },
    [SYSTEM_UPDATE_STATUS]: (state, action) => {
      return {
        ...state,
        status: mapToAsyncState<SystemStatusResult | undefined>(
          action,
          state.status.items
        ),
      };
    },
    [SYSTEM_UPDATE_TASKS]: (state, action) => {
      return {
        ...state,
        tasks: mapToAsyncState<Array<SystemTaskResult>>(
          action,
          state.tasks.items
        ),
      };
    },
    [SYSTEM_RUN_TASK]: (state, action: Action<string>) => {
      const id = action.payload;
      const tasks = state.tasks;
      const newItems = [...tasks.items];

      const idx = newItems.findIndex((v) => v.job_id === id);

      if (idx !== -1) {
        newItems[idx].job_running = true;
      }

      return {
        ...state,
        tasks: {
          ...tasks,
          items: newItems,
        },
      };
    },
    [PROVIDER_UPDATE_LIST]: (state, action) => {
      return {
        ...state,
        providers: mapToAsyncState(action, state.providers.items),
      };
    },
    [SYSTEM_UPDATE_LOGS]: (state, action) => {
      return {
        ...state,
        logs: mapToAsyncState(action, state.logs.items),
      };
    },
    [SYSTEM_UPDATE_RELEASES]: (state, action) => {
      return {
        ...state,
        releases: mapToAsyncState(action, state.releases.items),
      };
    },
    [SYSTEM_UPDATE_SETTINGS]: (state, action) => {
      return {
        ...state,
        settings: mapToAsyncState(action, state.settings.items),
      };
    },
  },
  {
    languages: { updating: true, items: [] },
    enabledLanguage: { updating: true, items: [] },
    languagesProfiles: { updating: true, items: [] },
    status: {
      updating: true,
      items: undefined,
    },
    tasks: {
      updating: true,
      items: [],
    },
    providers: {
      updating: true,
      items: [],
    },
    logs: {
      updating: true,
      items: [],
    },
    releases: {
      updating: true,
      items: [],
    },
    settings: {
      updating: true,
      items: undefined,
    },
  }
);

export default reducer;
