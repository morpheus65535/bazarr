import {
  SYSTEM_UPDATE_LANGUAGES_LIST,
  SYSTEM_UPDATE_ENABLED_LANGUAGES_LIST,
  SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST,
  SYSTEM_UPDATE_SYSTEM_STATUS,
  SYSTEM_UPDATE_SYSTEM_TASKS,
  PROVIDER_UPDATE_LIST,
  SYSTEM_UPDATE_SYSTEM_LOGS,
  SYSTEM_UPDATE_SYSTEM_SETTINGS,
} from "../constants";
import { mapToAsyncState } from "./mapper";

import { handleActions } from "redux-actions";

const reducer = handleActions<SystemState, any>(
  {
    [SYSTEM_UPDATE_LANGUAGES_LIST]: {
      next(state, action) {
        const newState = {
          ...state,
          languages: mapToAsyncState<Array<Language>>(action, []),
        };
        return newState;
      },
    },
    [SYSTEM_UPDATE_ENABLED_LANGUAGES_LIST]: {
      next(state, action) {
        const newState = {
          ...state,
          enabledLanguage: mapToAsyncState<Array<Language>>(action, []),
        };
        return newState;
      },
    },
    [SYSTEM_UPDATE_LANGUAGES_PROFILE_LIST]: {
      next(state, action) {
        const newState = {
          ...state,
          languagesProfiles: mapToAsyncState<Array<LanguagesProfile>>(
            action,
            []
          ),
        };
        return newState;
      },
    },
    [SYSTEM_UPDATE_SYSTEM_STATUS]: {
      next(state, action) {
        return {
          ...state,
          status: mapToAsyncState<SystemStatusResult | undefined>(
            action,
            state.status.items
          ),
        };
      },
    },
    [SYSTEM_UPDATE_SYSTEM_TASKS]: {
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
    [PROVIDER_UPDATE_LIST]: {
      next(state, action) {
        return {
          ...state,
          providers: mapToAsyncState(action, state.providers.items),
        };
      },
    },
    [SYSTEM_UPDATE_SYSTEM_LOGS]: {
      next(state, action) {
        return {
          ...state,
          logs: mapToAsyncState(action, state.logs.items),
        };
      },
    },
    [SYSTEM_UPDATE_SYSTEM_SETTINGS]: {
      next(state, action) {
        return {
          ...state,
          settings: mapToAsyncState(action, state.settings.items),
        };
      },
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
    settings: {
      updating: true,
      items: undefined,
    },
  }
);

export default reducer;
