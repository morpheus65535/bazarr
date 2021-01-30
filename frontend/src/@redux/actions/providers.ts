import { createAsyncAction, createCombineAction } from "./utils";
import { PROVIDER_UPDATE_LIST } from "../constants";

import { badgeUpdateProviders } from "./badges";

import { ProvidersApi } from "../../apis";

export const providerUpdateList = createAsyncAction(PROVIDER_UPDATE_LIST, () =>
  ProvidersApi.providers()
);

export const providerUpdateAll = createCombineAction(() => [
  providerUpdateList(),
  badgeUpdateProviders(),
]);
