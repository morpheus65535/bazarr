import {
  ActionReducerMapBuilder,
  AsyncThunk,
  CaseReducer,
  Draft,
} from "@reduxjs/toolkit";
import { AsyncThunkFulfilledActionCreator } from "@reduxjs/toolkit/dist/createAsyncThunk";
import { difference, has, uniqBy } from "lodash";

export function createAOSReducer<S, T, ID extends keyof T>(
  builder: ActionReducerMapBuilder<S>,
  thunk: AsyncThunk<AsyncDataWrapper<T>, number[], {}>,
  getAos: (state: Draft<S>) => Draft<AsyncOrderState<T>>,
  match: ID
) {
  builder
    .addCase(thunk.pending, (state, action) => {
      const aos = getAos(state);
      aos.state = "loading";
    })
    .addCase(thunk.fulfilled, (state, action) => {
      const aos = getAos(state);
      aos.state = "succeeded";
    })
    .addCase(thunk.rejected, (state, action) => {
      const aos = getAos(state);
      aos.state = "failed";
      aos.error = action.error as Error;
    });
}

export function createAOSWholeReducer<S, T, ID extends keyof T>(
  builder: ActionReducerMapBuilder<S>,
  thunk: AsyncThunk<AsyncDataWrapper<T>, number[] | undefined, {}>,
  getAos: (state: Draft<S>) => Draft<AsyncOrderState<T>>,
  match: ID
) {
  builder
    .addCase(thunk.pending, (state, action) => {
      const aos = getAos(state);
      aos.state = "loading";
    })
    .addCase(thunk.fulfilled, (state, action) => {
      const aos = getAos(state);
      aos.state = "succeeded";
    })
    .addCase(thunk.rejected, (state, action) => {
      const aos = getAos(state);
      aos.state = "failed";
      aos.error = action.error as Error;
    });
}

export function createAOSRangeReducer<S, T>(
  builder: ActionReducerMapBuilder<S>,
  thunk: AsyncThunk<AsyncDataWrapper<T>, ReduxStore.ByRangePayload, {}>,
  getAos: (state: Draft<S>) => Draft<AsyncOrderState<T>>
) {
  builder
    .addCase(thunk.pending, (state, action) => {
      const aos = getAos(state);
      aos.state = "loading";
    })
    .addCase(thunk.fulfilled, (state, action) => {
      const aos = getAos(state);
      aos.state = "succeeded";
    })
    .addCase(thunk.rejected, (state, action) => {
      const aos = getAos(state);
      aos.state = "failed";
      aos.error = action.error as Error;
    });
}

export function removeOrderListItem<T extends LooseObject>(
  state: Draft<AsyncOrderState<T>>,
  action: ReduxStore.Action<number[]>
) {
  const ids = action.payload;
  const { items, order } = state.data;
  ids.forEach((v) => {
    if (has(items, v)) {
      delete items[v];
    }
  });
  state.data.order = difference(order, ids);
}

export function removeAsyncListItem<T extends LooseObject>(
  state: Draft<AsyncState<T[]>>,
  action: ReduxStore.Action<number[]>,
  match: ItemIdType<T>
) {
  const ids = new Set(action.payload);
  state.data = state.data.filter((v) => !ids.has((v as T)[match]));
}

export function createAsyncStateReducer<
  S,
  T extends Array<any> | LooseObject,
  TT extends Array<any> | LooseObject = T
>(
  builder: ActionReducerMapBuilder<S>,
  thunk: AsyncThunk<TT, void, {}>,
  getAsync: (state: Draft<S>) => Draft<AsyncState<T | undefined | null>>,
  fulfilled?: CaseReducer<
    S,
    ReturnType<AsyncThunkFulfilledActionCreator<TT, void, {}>>
  >
) {
  builder
    .addCase(thunk.pending, (state) => {
      const as = getAsync(state);
      as.state = "loading";
      as.error = undefined;
    })
    .addCase(thunk.fulfilled, (state, action) => {
      if (fulfilled !== undefined) {
        fulfilled(state, action);
      } else {
        const as = getAsync(state);
        as.state = "succeeded";
        as.data = action.payload as Draft<T>;
      }
    })
    .addCase(thunk.rejected, (state, action) => {
      const as = getAsync(state);
      as.state = "failed";
      as.error = action.error as Error;
    });
}

export function createAsyncListReducer<S, T, ID extends keyof T>(
  builder: ActionReducerMapBuilder<S>,
  thunk: AsyncThunk<T[], number[], {}>,
  getAsync: (state: Draft<S>) => Draft<AsyncState<T[]>>,
  match: ID
) {
  builder
    .addCase(thunk.pending, (state) => {
      const as = getAsync(state);
      as.state = "loading";
      as.error = undefined;
    })
    .addCase(thunk.fulfilled, (state, action) => {
      const as = getAsync(state);
      as.state = "succeeded";
      const olds = as.data as T[];
      const news = action.payload as T[];
      as.data = uniqBy([...news, ...olds], match) as Draft<T>[];
    })
    .addCase(thunk.rejected, (state, action) => {
      const as = getAsync(state);
      as.state = "failed";
      as.error = action.error as Error;
    });
}

// export function updateOrderIdState<T extends LooseObject>(
//   action: AsyncAction<AsyncDataWrapper<T>>,
//   state: AsyncOrderState<T>,
//   id: ItemIdType<T>
// ): AsyncOrderState<T> {
//   if (action.payload.loading) {
//     return {
//       data: {
//         ...state.data,
//         dirty: true,
//       },
//       fetching: true,
//     };
//   } else if (action.error !== undefined) {
//     return {
//       data: {
//         ...state.data,
//         dirty: true,
//       },
//       fetching: false,
//       error: action.payload.item as Error,
//     };
//   } else {
//     const { data, total } = action.payload.item as AsyncDataWrapper<T>;
//     const { parameters } = action.payload;
//     const [start, length] = parameters;

//     // Convert item list to object
//     const newItems = data.reduce<IdState<T>>(
//       (prev, curr) => {
//         const tid = curr[id];
//         prev[tid] = curr;
//         return prev;
//       },
//       { ...state.data.items }
//     );

//     let newOrder = [...state.data.order];

//     const countDist = total - newOrder.length;
//     if (countDist > 0) {
//       newOrder = Array(countDist).fill(null).concat(newOrder);
//     } else if (countDist < 0) {
//       // Completely drop old data if list has shrinked
//       newOrder = Array(total).fill(null);
//     }

//     const idList = newOrder.filter(isNumber);

//     const dataOrder: number[] = data.map((v) => v[id]);

//     if (typeof start === "number" && typeof length === "number") {
//       newOrder.splice(start, length, ...dataOrder);
//     } else if (isArray(start)) {
//       // Find the null values and delete them, insert new values to the front of array
//       const addition = difference(dataOrder, idList);
//       let addCount = addition.length;
//       newOrder.unshift(...addition);

//       newOrder = newOrder.flatMap((v) => {
//         if (isNull(v) && addCount > 0) {
//           --addCount;
//           return [];
//         } else {
//           return [v];
//         }
//       }, []);

//       conditionalLog(
//         addCount !== 0,
//         "Error when replacing item in OrderIdState"
//       );
//     } else if (parameters.length === 0) {
//       // TODO: Delete me -> Full Update
//       newOrder = dataOrder;
//     }

//     return {
//       fetching: false,
//       data: {
//         dirty: true,
//         items: newItems,
//         order: newOrder,
//       },
//     };
//   }
// }

// export function deleteOrderListItemBy<T extends LooseObject>(
//   action: Action<number[]>,
//   state: AsyncOrderState<T>
// ): AsyncOrderState<T> {
//   const ids = action.payload;
//   const { items, order } = state.data;
//   const newItems = { ...items };
//   ids.forEach((v) => {
//     if (has(newItems, v)) {
//       delete newItems[v];
//     }
//   });
//   const newOrder = difference(order, ids);
//   return {
//     ...state,
//     data: {
//       dirty: true,
//       items: newItems,
//       order: newOrder,
//     },
//   };
// }

// export function deleteAsyncListItemBy<T extends LooseObject>(
//   action: Action<number[]>,
//   state: AsyncState<T[]>,
//   match: ItemIdType<T>
// ): AsyncState<T[]> {
//   const ids = new Set(action.payload);
//   const data = [...state.data].filter((v) => !ids.has(v[match]));
//   return {
//     ...state,
//     data,
//   };
// }
