import { difference, has, isArray, isNull, isNumber, uniqBy } from "lodash";
import { Action } from "redux-actions";
import { conditionalLog } from "../../utilites/logger";
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
  state: AsyncOrderState<T>,
  id: ItemIdType<T>
): AsyncOrderState<T> {
  if (action.payload.loading) {
    return {
      data: {
        ...state.data,
        fetched: true,
      },
      updating: true,
    };
  } else if (action.error !== undefined) {
    return {
      data: {
        ...state.data,
        fetched: true,
      },
      updating: false,
      error: action.payload.item as Error,
    };
  } else {
    const { data, total } = action.payload.item as AsyncDataWrapper<T>;
    const { parameters } = action.payload;
    const [start, length] = parameters;

    // Convert item list to object
    const newItems = data.reduce<IdState<T>>(
      (prev, curr) => {
        const tid = curr[id];
        prev[tid] = curr;
        return prev;
      },
      { ...state.data.items }
    );

    let newOrder = [...state.data.order];

    const countDist = total - newOrder.length;
    if (countDist > 0) {
      newOrder = Array(countDist).fill(null).concat(newOrder);
    } else if (countDist < 0) {
      // Completely drop old data if list has shrinked
      newOrder = Array(total).fill(null);
    }

    const idList = newOrder.filter(isNumber);

    const dataOrder: number[] = data.map((v) => v[id]);

    if (typeof start === "number" && typeof length === "number") {
      newOrder.splice(start, length, ...dataOrder);
    } else if (isArray(start)) {
      // Find the null values and delete them, insert new values to the front of array
      const addition = difference(dataOrder, idList);
      let addCount = addition.length;
      newOrder.unshift(...addition);

      newOrder = newOrder.flatMap((v) => {
        if (isNull(v) && addCount > 0) {
          --addCount;
          return [];
        } else {
          return [v];
        }
      }, []);

      conditionalLog(
        addCount !== 0,
        "Error when replacing item in OrderIdState"
      );
    } else if (parameters.length === 0) {
      // TODO: Delete me -> Full Update
      newOrder = dataOrder;
    }

    return {
      updating: false,
      data: {
        fetched: true,
        items: newItems,
        order: newOrder,
      },
    };
  }
}

export function deleteOrderListItemBy<T extends LooseObject>(
  action: Action<number[]>,
  state: AsyncOrderState<T>
): AsyncOrderState<T> {
  const ids = action.payload;
  const { items, order } = state.data;
  const newItems = { ...items };
  ids.forEach((v) => {
    if (has(newItems, v)) {
      delete newItems[v];
    }
  });
  const newOrder = difference(order, ids);
  return {
    ...state,
    data: {
      fetched: true,
      items: newItems,
      order: newOrder,
    },
  };
}

export function deleteAsyncListItemBy<T extends LooseObject>(
  action: Action<number[]>,
  state: AsyncState<T[]>,
  match: ItemIdType<T>
): AsyncState<T[]> {
  const ids = new Set(action.payload);
  const data = [...state.data].filter((v) => !ids.has(v[match]));
  return {
    ...state,
    data,
  };
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
