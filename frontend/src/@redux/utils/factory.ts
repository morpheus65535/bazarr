import {
  ActionCreatorWithoutPayload,
  ActionCreatorWithPayload,
  ActionReducerMapBuilder,
  AsyncThunk,
  Draft,
} from "@reduxjs/toolkit";
import {
  difference,
  differenceWith,
  findIndex,
  has,
  isNull,
  isString,
  uniq,
} from "lodash";
import { conditionalLog } from "../../utilites/logger";

interface ActionParam<T, ID = null> {
  range?: AsyncThunk<T, Parameter.Range, {}>;
  all?: AsyncThunk<T, void, {}>;
  ids?: AsyncThunk<T, ID[], {}>;
  removeIds?: ActionCreatorWithPayload<ID[]>;
  dirty?: ID extends null
    ? ActionCreatorWithoutPayload
    : ActionCreatorWithPayload<ID[]>;
}

export function createAsyncItemReducer<S, T>(
  builder: ActionReducerMapBuilder<S>,
  actions: Pick<ActionParam<T>, "all" | "dirty">,
  getItem: (state: Draft<S>) => Draft<Async.Item<T>>
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
      if (!isNull(item.content)) {
        item.state = "dirty";
      }
    });
}

export function createAsyncListReducer<
  S,
  ID extends Async.IdType,
  T extends { [key in K]: ID },
  K extends keyof T
>(
  builder: ActionReducerMapBuilder<S>,
  getList: (state: Draft<S>) => Draft<Async.List<T>>,
  idKey: K,
  actions: ActionParam<T[], ID>
) {
  const { ids, removeIds, all, dirty } = actions;
  ids &&
    builder
      .addCase(ids.pending, (state) => {
        const item = getList(state);
        item.state = "loading";
        item.error = null;
      })
      .addCase(ids.fulfilled, (state, action) => {
        const item = getList(state);

        action.payload.forEach((v) => {
          const idx = findIndex(
            item.content,
            (d) => (d as T)[idKey] === v[idKey]
          );
          if (idx !== -1) {
            item.content.splice(idx, 1, v as Draft<T>);
          } else {
            item.content.unshift(v as Draft<T>);
          }
        });

        item.dirtyEntities = difference(item.dirtyEntities, action.meta.arg);

        if (item.dirtyEntities.length > 0) {
          item.state = "dirty";
        } else {
          item.state = "succeeded";
        }
      })
      .addCase(ids.rejected, (state, action) => {
        const item = getList(state);
        item.state = "failed";
        item.error = action.error.message ?? null;
      });

  removeIds &&
    builder.addCase(removeIds, (state, action) => {
      const item = getList(state);
      item.content = differenceWith(
        item.content,
        action.payload,
        (lhs, rhs) => {
          return (lhs as T)[idKey] === rhs;
        }
      );
      item.dirtyEntities = difference(item.dirtyEntities, action.payload);
      if (item.state === "dirty" && item.dirtyEntities.length === 0) {
        item.state = "succeeded";
      }
    });

  all &&
    builder
      .addCase(all.pending, (state) => {
        const item = getList(state);
        item.state = "loading";
        item.error = null;
      })
      .addCase(all.fulfilled, (state, action) => {
        const item = getList(state);
        item.state = "succeeded";
        item.content = action.payload as Draft<T[]>;
        item.dirtyEntities = [];
      })
      .addCase(all.rejected, (state, action) => {
        const item = getList(state);
        item.state = "failed";
        item.error = action.error.message ?? null;
      });

  dirty &&
    builder.addCase(dirty, (state, action) => {
      const item = getList(state);
      item.state = "dirty";
      item.dirtyEntities.push(...action.payload);
      item.dirtyEntities = uniq(item.dirtyEntities);
    });
}

export function createAsyncEntityReducer<S, T, ID extends Async.IdType>(
  builder: ActionReducerMapBuilder<S>,
  getEntity: (state: Draft<S>) => Draft<Async.Entity<T>>,
  actions: ActionParam<AsyncDataWrapper<T>, ID>
) {
  const { all, removeIds, ids, range, dirty } = actions;

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

        const {
          content: { keyName },
        } = entity;

        const idsToAdd = data.map((v) => String(v[keyName as keyof T]));

        if (entity.content.ids.length < total) {
          const size = total - entity.content.ids.length;
          entity.content.ids.push(...Array(size).fill(null));
        } else if (entity.content.ids.length > total) {
          const idSize = entity.content.ids.length;
          const size = idSize - total;
          const start = idSize - size;
          const deleted = entity.content.ids.splice(start, size);
          deleted.forEach((v) => {
            if (v) {
              delete entity.content.entities[v];
            }
          });
        }

        entity.dirtyEntities = difference(
          entity.dirtyEntities,
          idsToAdd as Draft<string>[]
        );
        entity.content.ids.splice(start, length, ...idsToAdd);
        data.forEach((v) => {
          const key = String(v[keyName as keyof T]);
          entity.content.entities[key] = v as Draft<T>;
        });

        if (entity.dirtyEntities.length > 0) {
          entity.state = "dirty";
        } else {
          entity.state = "succeeded";
        }
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
          payload: { data, total },
        } = action;

        const {
          content: { keyName },
        } = entity;

        const idsToAdd = data.map((v) => String(v[keyName as keyof T]));

        const addedIds = difference(
          idsToAdd,
          entity.content.ids.filter(isString)
        );
        entity.content.ids.unshift(...addedIds);

        if (entity.content.ids.length < total) {
          const size = total - entity.content.ids.length;
          entity.content.ids.push(...Array(size).fill(null));
        } else if (entity.content.ids.length > total) {
          const idSize = entity.content.ids.length;
          const size = idSize - total;
          const start = idSize - size;
          const deleted = entity.content.ids
            .splice(start, size)
            .filter(isString);
          deleted.forEach((v) => {
            delete entity.content.entities[v];
          });
        }

        entity.dirtyEntities = difference(
          entity.dirtyEntities,
          idsToAdd as Draft<string>[]
        );

        if (entity.dirtyEntities.length > 0) {
          entity.state = "dirty";
        } else {
          entity.state = "succeeded";
        }

        data.forEach((v) => {
          const key = String(v[keyName as keyof T]);
          entity.content.entities[key] = v as Draft<T>;
        });
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

      const idsToDelete = action.payload.map((v) => v.toString());

      entity.content.ids = difference(
        entity.content.ids,
        idsToDelete as Draft<string>[]
      );
      entity.dirtyEntities = difference(
        entity.dirtyEntities,
        idsToDelete as Draft<string>[]
      );

      if (entity.state === "dirty" && entity.dirtyEntities.length === 0) {
        entity.state = "succeeded";
      }

      idsToDelete.forEach((v) => {
        if (has(entity.content.entities, v)) {
          delete entity.content.entities[v];
        }
      });
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

        const {
          content: { keyName },
        } = entity;

        entity.state = "succeeded";
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

  dirty &&
    builder.addCase(dirty, (state, action) => {
      const entity = getEntity(state);
      entity.state = "dirty";
      const dirtyIds = action.payload.map((v: string | number) => v.toString());
      entity.dirtyEntities.push(...dirtyIds);
      entity.dirtyEntities = uniq(entity.dirtyEntities);
    });
}
