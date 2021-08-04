import {
  ActionCreatorWithPayload,
  ActionReducerMapBuilder,
  AsyncThunk,
  Draft,
  PayloadAction,
} from "@reduxjs/toolkit";
import { difference, differenceWith, findIndex, has } from "lodash";

export function createAsyncItemReducer<S, T>(
  builder: ActionReducerMapBuilder<S>,
  thunk: AsyncThunk<T, void, {}>,
  getItem: (state: Draft<S>) => Draft<Async.Item<T>>
) {
  builder
    .addCase(thunk.pending, (state, action) => {
      const item = getItem(state);
      item.state = "loading";
    })
    .addCase(thunk.fulfilled, (state, action) => {
      const item = getItem(state);
      item.state = "succeeded";
      item.content = action.payload as Draft<T>;
    })
    .addCase(thunk.rejected, (state, action) => {
      const item = getItem(state);
      item.state = "failed";
      item.error = action.error;
    });
}

export function createAsyncListReducer<S, T>(
  builder: ActionReducerMapBuilder<S>,
  thunk: AsyncThunk<T[], void, {}>,
  getList: (state: Draft<S>) => Draft<Async.List<T>>
) {
  builder
    .addCase(thunk.pending, (state, action) => {
      const item = getList(state);
      item.state = "loading";
    })
    .addCase(thunk.fulfilled, (state, action) => {
      const item = getList(state);
      item.state = "succeeded";
      item.content = action.payload as Draft<T[]>;
      item.dirtyEntities = [];
    })
    .addCase(thunk.rejected, (state, action) => {
      const item = getList(state);
      item.state = "failed";
      item.error = action.error;
    });
}

export function createAsyncListIdReducer<
  S,
  ID extends Async.IdType,
  K extends keyof T,
  T extends { [key in K]: ID }
>(
  builder: ActionReducerMapBuilder<S>,
  getList: (state: Draft<S>) => Draft<Async.List<T>>,
  idKey: K,
  update: AsyncThunk<T[], ID[], {}>,
  remove?: ActionCreatorWithPayload<ID[]>
) {
  builder
    .addCase(update.pending, (state) => {
      const item = getList(state);
      item.state = "loading";
    })
    .addCase(update.fulfilled, (state, action) => {
      const item = getList(state);
      item.state = "succeeded";

      action.payload.forEach((v) => {
        const idx = findIndex(
          item.content,
          (d) => (d as T)[idKey] === v[idKey]
        );
        if (idx !== -1) {
          item.content[idx] = v as Draft<T>;
        }
      });

      item.dirtyEntities = difference(item.dirtyEntities, action.meta.arg);
    })
    .addCase(update.rejected, (state, action) => {
      const item = getList(state);
      item.state = "failed";
      item.error = action.error;
    });

  if (remove) {
    builder.addCase(remove, (state, action) => {
      const item = getList(state);
      item.content = differenceWith(
        item.content,
        action.payload,
        (lhs, rhs) => {
          return (lhs as T)[idKey] === rhs;
        }
      );
    });
  }
}

// OLD down below

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
  thunk: AsyncThunk<AsyncDataWrapper<T>, Parameter.Range, {}>,
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
  action: PayloadAction<number[]>
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
