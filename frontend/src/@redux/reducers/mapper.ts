import { uniqBy } from "lodash";
import { AsyncAction } from "../types";

export function updateAsyncState<Payload>(
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

export function updateOrderIdState<T extends LooseObject>(
  action: AsyncAction<AsyncDataWrapper<T>>,
  state: AsyncState<OrderIdState<T>>,
  id: ItemIdType<T>
): AsyncState<OrderIdState<T>> {
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
    const { data, total } = action.payload.item as AsyncDataWrapper<T>;
    const [start, length] = action.payload.parameters;

    // Convert item list to object
    const idState: IdState<T> = data.reduce<IdState<T>>((prev, curr) => {
      const tid = curr[id];
      prev[tid] = curr;
      return prev;
    }, {});

    const dataOrder: number[] = data.map((v) => v[id]);

    let newItems = { ...state.data.items, ...idState };
    let newOrder = state.data.order;

    const countDist = total - newOrder.length;
    if (countDist > 0) {
      newOrder.push(...Array(countDist).fill(null));
    } else if (countDist < 0) {
      // Completely drop old data if list has shrinked
      newOrder = Array(total).fill(null);
      newItems = { ...idState };
    }

    if (typeof start === "number" && typeof length === "number") {
      newOrder.splice(start, length, ...dataOrder);
    } else if (start === undefined) {
      // Full Update
      newOrder = dataOrder;
    }

    return {
      updating: false,
      data: {
        items: newItems,
        order: newOrder,
      },
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
    const olds = state.data as T[];
    const news = action.payload.item as T[];

    const result = uniqBy([...news, ...olds], match);

    return {
      updating: false,
      data: result,
    };
  }
}
