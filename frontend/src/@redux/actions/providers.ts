import { ProvidersApi } from "../../apis";
import { PROVIDER_UPDATE_LIST } from "../constants";
import { createAsyncAction } from "./factory";

export const providerUpdateList = createAsyncAction(PROVIDER_UPDATE_LIST, () =>
  ProvidersApi.providers()
);
