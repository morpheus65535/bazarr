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
      error: (action.payload.item as Error).message,
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
      error: (action.payload.item as Error).message,
    };
  } else {
    const list = [...(state.items as T[])];
    const payload = action.payload.item as T[];

    payload.forEach((v) => {
      const idx = list.findIndex((old) => old[match] === v[match]);

      if (idx !== -1) {
        list[idx] = v;
      }
    });

    return {
      updating: false,
      items: list,
    };
  }
}
