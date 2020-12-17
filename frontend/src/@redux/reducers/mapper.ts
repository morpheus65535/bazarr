import { AsyncAction } from "../types";
import { clone } from "lodash"

export function mapToAsyncState<Payload>(
  action: AsyncAction<Payload>,
  defVal: Payload
): AsyncState<Payload> {
  if (action.payload.loading) {
    return {
      updating: true,
      lastResult: undefined,
      items: defVal,
    };
  } else if (action.error !== undefined) {
    return {
      updating: false,
      lastResult: action.payload.item as string,
      items: defVal,
    };
  } else {
    return {
      updating: false,
      lastResult: undefined,
      items: action.payload.item as Payload,
    };
  }
}

export function updateAsyncList<T, ID extends keyof T>(
  action: AsyncAction<Array<T>>,
  state: AsyncState<Array<T>>,
  match: ID
): AsyncState<Array<T>> {
  if (action.payload.loading) {
    return {
      ...state,
      updating: true,
      lastResult: undefined,
    };
  } else if (action.error !== undefined) {
    return {
      ...state,
      updating: false,
      lastResult: action.payload.item as string,
    };
  } else {
    // Deep Copy
    // TODO: Opti Performance
    const payload = action.payload.item as Array<T>;
    const items = state.items.map((val) => {
      const idx = payload.findIndex((old) => old[match] === val[match])
      if (idx !== -1) {
        return payload[idx]
      } else {
        return val
      }
    })
    return {
      updating: false,
      lastResult: undefined,
      items
    };
  }
}
