import { ProvidersApi } from "../../apis";
import { PROVIDER_UPDATE_LIST } from "../constants";
import { createAsyncAction, createCombineAction } from "./factory";
import { badgeUpdateAll } from "./site";

const providerUpdateList = createAsyncAction(PROVIDER_UPDATE_LIST, () =>
  ProvidersApi.providers()
);

export const providerUpdateAll = createCombineAction(() => [
  providerUpdateList(),
  badgeUpdateAll(),
]);
