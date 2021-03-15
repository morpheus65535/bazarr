import { isNullable, mergeArray } from "../../utilites";
import { AsyncAction } from "../types";

export function mapToAsyncState<Payload>(
  action: AsyncAction<Payload>,
  defVal: Readonly<Payload>
): AsyncState<Payload> {
  if (action.payload.loading) {
    return {
      updating: true,
      data: defVal,
    };
  } else if (action.error !== undefined) {
    return {
      updating: false,
      error: action.payload.item as Error,
      data: defVal,
    };
  } else {
    return {
      updating: false,
      error: undefined,
      data: action.payload.item as Payload,
    };
  }
}

export function updateAsyncDataList<T, ID extends keyof T>(
  action: AsyncAction<AsyncDataWrapper<T>>,
  state: AsyncState<Nullable<T>[]>,
  match: ID
): AsyncState<Nullable<T>[]> {
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
    const payload = action.payload.item as AsyncDataWrapper<T>;
    const [start, length] = action.payload.parameters;
    const { data, total } = payload;

    let result: Nullable<T>[] = [];

    const list = [...state.data];

    // Fill empty list with null
    const fillCount = total - list.length;
    if (fillCount > 0) {
      list.push(...Array(fillCount).fill(null));
    } else if (fillCount < 0) {
      throw new Error("array in redux storage is larger then API total");
    }

    if (typeof start === "number" && typeof length === "number") {
      result = list;

      // TODO: Performance
      // Remove duplicate item
      result.filter((v) => {
        if (!isNullable(v)) {
          return data.find((inn) => inn[match] === v[match]) === undefined;
        } else {
          return true;
        }
      });

      result.splice(start, data.length, ...data);
    } else {
      result = mergeArray(list, data, (l, r) => l[match] === r[match]);
    }

    return {
      updating: false,
      data: result,
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
    const list = state.data as T[];
    const payload = action.payload.item as T[];
    const result = mergeArray(list, payload, (l, r) => l[match] === r[match]);

    return {
      updating: false,
      data: result,
    };
  }
}
