import {
  ActionCreatorWithPayload,
  ActionReducerMapBuilder,
  AsyncThunk,
  Draft,
} from "@reduxjs/toolkit";
import { difference, differenceWith, findIndex, has } from "lodash";
import { conditionalLog } from "../../utilites/logger";

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
      item.error = action.error.message ?? null;
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
      item.error = action.error.message ?? null;
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
        } else {
          item.content.push(v as Draft<T>);
        }
      });

      item.dirtyEntities = difference(item.dirtyEntities, action.meta.arg);
    })
    .addCase(update.rejected, (state, action) => {
      const item = getList(state);
      item.state = "failed";
      item.error = action.error.message ?? null;
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

export function createAsyncEntityReducer<S, T, ID extends Async.IdType>(
  builder: ActionReducerMapBuilder<S>,
  getEntity: (state: Draft<S>) => Draft<Async.Entity<T>>,
  range: AsyncThunk<AsyncDataWrapper<T>, Parameter.Range, {}>,
  itemId: AsyncThunk<AsyncDataWrapper<T>, ID[], {}>,
  remove: ActionCreatorWithPayload<ID[]>,
  all?: AsyncThunk<AsyncDataWrapper<T>, void, {}>
) {
  builder
    .addCase(range.pending, (state) => {
      const entity = getEntity(state);
      entity.state = "loading";
    })
    .addCase(range.fulfilled, (state, action) => {
      const entity = getEntity(state);
      entity.state = "succeeded";

      const {
        meta: {
          arg: { start, length },
        },
        payload: { data, total },
      } = action;

      let {
        content: { keyName, entities, ids },
        dirtyEntities,
      } = entity;

      const idsToAdd = data.map((v) => String(v[keyName as keyof T]));

      if (ids.length < total) {
        const size = total - ids.length;
        ids.push(...Array(size).fill(null));
      }

      conditionalLog(
        ids.length !== total,
        "Error when building entity, size of id array mismatch"
      );

      entity.dirtyEntities = difference(
        dirtyEntities,
        idsToAdd as Draft<string>[]
      );
      ids.splice(start, length, ...idsToAdd);
      data.forEach((v) => {
        const key = String(v[keyName as keyof T]);
        entities[key] = v as Draft<T>;
      });
    })
    .addCase(range.rejected, (state, action) => {
      const entity = getEntity(state);
      entity.state = "failed";
      entity.error = action.error.message ?? null;
    });

  builder
    .addCase(itemId.pending, (state) => {
      const entity = getEntity(state);
      entity.state = "loading";
    })
    .addCase(itemId.fulfilled, (state, action) => {
      const entity = getEntity(state);
      entity.state = "succeeded";

      const {
        meta: { arg },
        payload: { data, total },
      } = action;

      let {
        content: { keyName, entities, ids },
        dirtyEntities,
      } = entity;

      const idsToAdd = arg.map((v) => v.toString());

      if (ids.length < total) {
        const size = total - ids.length;
        ids.push(...Array(size).fill(null));
      }

      conditionalLog(
        ids.length !== total,
        "Error when building entity, size of id array mismatch"
      );

      entity.dirtyEntities = difference(
        dirtyEntities,
        idsToAdd as Draft<string>[]
      );
      data.forEach((v) => {
        const key = String(v[keyName as keyof T]);
        entities[key] = v as Draft<T>;
      });
    })
    .addCase(itemId.rejected, (state, action) => {
      const entity = getEntity(state);
      entity.state = "failed";
      entity.error = action.error.message ?? null;
    });

  builder.addCase(remove, (state, action) => {
    const entity = getEntity(state);
    conditionalLog(
      entity.state === "loading",
      "Try to delete async entity when it's now loading"
    );

    const idsToDelete = action.payload.map((v) => v.toString());

    let {
      content: { ids, entities },
      dirtyEntities,
    } = entity;

    entity.content.ids = difference(ids, idsToDelete as Draft<string>[]);
    entity.dirtyEntities = difference(
      dirtyEntities,
      idsToDelete as Draft<string>[]
    );

    idsToDelete.forEach((v) => {
      if (has(entities, v)) {
        delete entities[v];
      }
    });
  });

  all &&
    builder
      .addCase(all.pending, (state, action) => {
        const entity = getEntity(state);
        entity.state = "loading";
      })
      .addCase(all.fulfilled, (state, action) => {
        const entity = getEntity(state);
        entity.state = "succeeded";

        const {
          payload: { data, total },
        } = action;

        conditionalLog(
          data.length !== total,
          "Length of data is mismatch with total length"
        );

        const {
          content: { keyName },
        } = entity;

        entity.dirtyEntities = [];
        entity.content.ids = data.map((v) => String(v[keyName as keyof T]));
        entity.content.entities = data.reduce<
          Draft<{
            [id: string]: T;
          }>
        >((prev, curr) => {
          const id = String(curr[keyName as keyof T]);
          prev[id] = curr as Draft<T>;
          return prev;
        }, {});
      })
      .addCase(all.rejected, (state, action) => {
        const entity = getEntity(state);
        entity.state = "failed";
        entity.error = action.error.message ?? null;
      });
}
