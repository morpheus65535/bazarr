import { mergeArray } from "../../utilites";
import { AsyncAction } from "../types";

export function mapToAsyncState<Payload>(
  action: AsyncAction<Payload>,
  defVal: Payload
): AsyncState<Payload> {
  if (action.payload.loading) {
    return {
      updating: true,
      items: defVal,
    };
  } else if (action.error !== undefined) {
    return {
      updating: false,
      error: action.payload.item as Error,
      items: defVal,
    };
  } else {
    return {
      updating: false,
      error: undefined,
      items: action.payload.item as Payload,
    };
  }
}

export function updateAsyncList<T, ID extends keyof T>(
  action: AsyncAction<T[]>,
  state: AsyncState<T[]>,
  match: ID
): AsyncState<T[]> {
  if (action.payload.loading) {
    return {
      ...state,
      updating: true,
    };
  } else if (action.error !== undefined) {
    return {
      ...state,
      updating: false,
      error: action.payload.item as Error,
    };
  } else {
    const list = state.items as T[];
    const payload = action.payload.item as T[];
    const result = mergeArray(list, payload, (l, r) => l[match] === r[match]);

    return {
      updating: false,
      items: result,
    };
  }
}
