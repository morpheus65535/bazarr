import { UPDATE_LANGUAGES_LIST, UPDATE_SYSTEM_STATUS } from "../constants";

import apis from "../../apis";
import { createAsyncAction } from "./creator";

export const updateLanguagesList = createAsyncAction(
  UPDATE_LANGUAGES_LIST,
  () => apis.system.languages()
);

export const UpdateSystemStatus = createAsyncAction(
  UPDATE_SYSTEM_STATUS,
  () => apis.system.status()
)