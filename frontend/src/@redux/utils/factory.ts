import {
  ActionCreatorWithoutPayload,
  ActionCreatorWithPayload,
  ActionReducerMapBuilder,
  AsyncThunk,
  Draft,
} from "@reduxjs/toolkit";
import {
  difference,
  findIndex,
  isNull,
  isString,
  omit,
  pullAll,
  pullAllWith,
} from "lodash";
import { ReducerUtility } from ".";
import { conditionalLog } from "../../utilities/logger";

interface ActionParam<T, ID = null> {
  range?: AsyncThunk<T, Parameter.Range, {}>;
  all?: AsyncThunk<T, void, {}>;
  ids?: AsyncThunk<T, ID[], {}>;
  removeIds?: ActionCreatorWithPayload<ID[]>;
  reset?: ActionCreatorWithoutPayload;
  dirty?: ID extends null
    ? ActionCreatorWithoutPayload
    : ActionCreatorWithPayload<ID[]>;
}

export function createAsyncItemReducer<S, T>(
  builder: ActionReducerMapBuilder<S>,
  getItem: (state: Draft<S>) => Draft<Async.Item<T>>,
  actions: Pick<ActionParam<T>, "all" | "dirty">
) {
  const { all, dirty } = actions;

  all &&
    builder
      .addCase(all.pending, (state) => {
        const item = getItem(state);
        item.state = "loading";
        item.error = null;
      })
      .addCase(all.fulfilled, (state, action) => {
        const item = getItem(state);
        item.state = "succeeded";
        item.content = action.payload as Draft<T>;
      })
      .addCase(all.rejected, (state, action) => {
        const item = getItem(state);
        item.state = "failed";
        item.error = action.error.message ?? null;
      });

  dirty &&
    builder.addCase(dirty, (state) => {
      const item = getItem(state);
      if (item.state !== "uninitialized") {
        item.state = "dirty";
      }
    });
}

export function createAsyncListReducer<S, T, ID extends Async.IdType>(
  builder: ActionReducerMapBuilder<S>,
  getList: (state: Draft<S>) => Draft<Async.List<T>>,
  actions: ActionParam<T[], ID>
) {
  const { ids, removeIds, all, dirty } = actions;
  ids &&
    builder
      .addCase(ids.pending, (state) => {
        const list = getList(state);
        list.state = "loading";
        list.error = null;
      })
      .addCase(ids.fulfilled, (state, action) => {
        const list = getList(state);

        const {
          meta: { arg },
        } = action;

        const strIds = arg.map(String);

        const keyName = list.keyName as keyof T;

        action.payload.forEach((v) => {
          const idx = findIndex(list.content, [keyName, v[keyName]]);
          if (idx !== -1) {
            list.content.splice(idx, 1, v as Draft<T>);
          } else {
            list.content.unshift(v as Draft<T>);
          }
        });

        ReducerUtility.updateDirty(list, strIds);
        ReducerUtility.updateDidLoaded(list, strIds);
      })
      .addCase(ids.rejected, (state, action) => {
        const list = getList(state);
        list.state = "failed";
        list.error = action.error.message ?? null;
      });

  removeIds &&
    builder.addCase(removeIds, (state, action) => {
      const list = getList(state);
      const keyName = list.keyName as keyof T;

      const removeIds = action.payload.map(String);

      pullAllWith(list.content, removeIds, (lhs, rhs) => {
        return String((lhs as T)[keyName]) === rhs;
      });

      ReducerUtility.removeDirty(list, removeIds);
      ReducerUtility.removeDidLoaded(list, removeIds);
    });

  all &&
    builder
      .addCase(all.pending, (state) => {
        const list = getList(state);
        list.state = "loading";
        list.error = null;
      })
      .addCase(all.fulfilled, (state, action) => {
        const list = getList(state);
        list.state = "succeeded";
        list.content = action.payload as Draft<T[]>;
        list.dirtyEntities = [];

        const ids = action.payload.map((v) =>
          String(v[list.keyName as keyof T])
        );
        ReducerUtility.updateDidLoaded(list, ids);
      })
      .addCase(all.rejected, (state, action) => {
        const list = getList(state);
        list.state = "failed";
        list.error = action.error.message ?? null;
      });

  dirty &&
    builder.addCase(dirty, (state, action) => {
      const list = getList(state);
      ReducerUtility.markDirty(list, action.payload.map(String));
    });
}

export function createAsyncEntityReducer<S, T, ID extends Async.IdType>(
  builder: ActionReducerMapBuilder<S>,
  getEntity: (state: Draft<S>) => Draft<Async.Entity<T>>,
  actions: ActionParam<AsyncDataWrapper<T>, ID>
) {
  const { all, removeIds, ids, range, dirty, reset } = actions;

  const checkSizeUpdate = (entity: Draft<Async.Entity<T>>, newSize: number) => {
    if (entity.content.ids.length !== newSize) {
      // Reset Entity State
      entity.dirtyEntities = [];
      entity.content.ids = Array(newSize).fill(null);
      entity.content.entities = {};
    }
  };

  range &&
    builder
      .addCase(range.pending, (state) => {
        const entity = getEntity(state);
        entity.state = "loading";
        entity.error = null;
      })
      .addCase(range.fulfilled, (state, action) => {
        const entity = getEntity(state);

        const {
          meta: {
            arg: { start, length },
          },
          payload: { data, total },
        } = action;

        const keyName = entity.content.keyName as keyof T;

        checkSizeUpdate(entity, total);

        data.forEach((v) => {
          const key = String(v[keyName]);
          entity.content.entities[key] = v as Draft<T>;
        });

        const idsToUpdate = data.map((v) => String(v[keyName]));

        // Remove duplicated ids
        const pulledSize =
          total - pullAll(entity.content.ids, idsToUpdate).length;
        entity.content.ids.push(...Array(pulledSize).fill(null));

        entity.content.ids.splice(start, length, ...idsToUpdate);

        ReducerUtility.updateDirty(entity, idsToUpdate);
        ReducerUtility.updateDidLoaded(entity, idsToUpdate);
      })
      .addCase(range.rejected, (state, action) => {
        const entity = getEntity(state);
        entity.state = "failed";
        entity.error = action.error.message ?? null;
      });

  ids &&
    builder
      .addCase(ids.pending, (state) => {
        const entity = getEntity(state);
        entity.state = "loading";
        entity.error = null;
      })
      .addCase(ids.fulfilled, (state, action) => {
        const entity = getEntity(state);

        const {
          meta: { arg },
          payload: { data, total },
        } = action;

        const keyName = entity.content.keyName as keyof T;

        checkSizeUpdate(entity, total);

        const idsToAdd = data.map((v) => String(v[keyName]));

        // For new ids, remove null from list and add them
        const newIds = difference(
          idsToAdd,
          entity.content.ids.filter(isString)
        );
        const newSize = entity.content.ids.unshift(...newIds);
        Array(newSize - total)
          .fill(undefined)
          .forEach(() => {
            const idx = entity.content.ids.findIndex(isNull);
            conditionalLog(idx === -1, "Error when deleting ids from entity");
            entity.content.ids.splice(idx, 1);
          });

        data.forEach((v) => {
          const key = String(v[keyName]);
          entity.content.entities[key] = v as Draft<T>;
        });

        const allIds = arg.map(String);

        ReducerUtility.updateDirty(entity, allIds);
        ReducerUtility.updateDidLoaded(entity, allIds);
      })
      .addCase(ids.rejected, (state, action) => {
        const entity = getEntity(state);
        entity.state = "failed";
        entity.error = action.error.message ?? null;
      });

  removeIds &&
    builder.addCase(removeIds, (state, action) => {
      const entity = getEntity(state);
      conditionalLog(
        entity.state === "loading",
        "Try to delete async entity when it's now loading"
      );

      const idsToDelete = action.payload.map(String);
      pullAll(entity.content.ids, idsToDelete);
      ReducerUtility.removeDirty(entity, idsToDelete);
      ReducerUtility.removeDidLoaded(entity, idsToDelete);

      omit(entity.content.entities, idsToDelete);
    });

  all &&
    builder
      .addCase(all.pending, (state) => {
        const entity = getEntity(state);
        entity.state = "loading";
        entity.error = null;
      })
      .addCase(all.fulfilled, (state, action) => {
        const entity = getEntity(state);

        const {
          payload: { data, total },
        } = action;

        conditionalLog(
          data.length !== total,
          "Length of data is mismatch with total length"
        );

        const keyName = entity.content.keyName as keyof T;

        entity.state = "succeeded";
        entity.dirtyEntities = [];
        entity.content.ids = data.map((v) => String(v[keyName]));
        entity.content.entities = data.reduce<
          Draft<{
            [id: string]: T;
          }>
        >((prev, curr) => {
          const id = String(curr[keyName]);
          prev[id] = curr as Draft<T>;
          return prev;
        }, {});

        const allIds = entity.content.ids.filter(isString);
        ReducerUtility.updateDidLoaded(entity, allIds);
      })
      .addCase(all.rejected, (state, action) => {
        const entity = getEntity(state);
        entity.state = "failed";
        entity.error = action.error.message ?? null;
      });

  dirty &&
    builder.addCase(dirty, (state, action) => {
      const entity = getEntity(state);
      ReducerUtility.markDirty(entity, action.payload.map(String));
    });

  reset &&
    builder.addCase(reset, (state) => {
      const entity = getEntity(state);
      entity.content.entities = {};
      entity.content.ids = [];
      entity.didLoaded = [];
      entity.dirtyEntities = [];
      entity.error = null;
      entity.state = "uninitialized";
    });
}
