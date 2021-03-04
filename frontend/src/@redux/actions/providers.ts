import { ProvidersApi } from "../../apis";
import { PROVIDER_UPDATE_LIST } from "../constants";
import { badgeUpdateProviders } from "./badges";
import { createAsyncAction, createCombineAction } from "./utils";

const providerUpdateList = createAsyncAction(PROVIDER_UPDATE_LIST, () =>
  ProvidersApi.providers()
);

export const providerUpdateAll = createCombineAction(() => [
  providerUpdateList(),
  badgeUpdateProviders(),
]);
