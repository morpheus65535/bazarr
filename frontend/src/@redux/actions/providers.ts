import { createAsyncAction, createCombineAction } from "./utils";
import { UPDATE_PROVIDER_LIST } from "../constants";

import { updateBadgeProviders } from "./badges";

import { ProvidersApi } from "../../apis";

export const UpdateProviderList = createAsyncAction(UPDATE_PROVIDER_LIST, () =>
  ProvidersApi.providers()
);

export const UpdateProvider = createCombineAction(() => [
  UpdateProviderList(),
  updateBadgeProviders(),
]);
