import { createAsyncAction } from "./creator";
import { UPDATE_PROVIDER_LIST } from "../constants";

import { ProvidersApi } from "../../apis";

export const UpdateProviderList = createAsyncAction(UPDATE_PROVIDER_LIST, () =>
  ProvidersApi.providers()
);
