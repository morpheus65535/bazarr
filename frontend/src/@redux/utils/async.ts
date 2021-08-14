import { Draft } from "@reduxjs/toolkit";
import { difference, uniq } from "lodash";

export namespace AsyncUtility {
  export function getDefaultItem<T>(): Async.Item<T> {
    return {
      state: "uninitialized",
      content: null,
      error: null,
    };
  }

  export function getDefaultList<T>(key: keyof T): Async.List<T> {
    return {
      state: "uninitialized",
      keyName: key,
      dirtyEntities: [],
      content: [],
      error: null,
    };
  }

  export function getDefaultEntity<T>(key: keyof T): Async.Entity<T> {
    return {
      state: "uninitialized",
      dirtyEntities: [],
      content: {
        keyName: key,
        ids: [],
        entities: {},
      },
      error: null,
    };
  }
}

export namespace AsyncReducer {
  type DirtyType = Draft<Async.Entity<any>> | Draft<Async.List<any>>;
  export function markDirty<T extends DirtyType>(
    entity: T,
    dirtyIds: string[]
  ) {
    if (entity.state !== "uninitialized" && entity.state !== "loading") {
      entity.state = "dirty";
      entity.dirtyEntities.push(...dirtyIds);
      entity.dirtyEntities = uniq(entity.dirtyEntities);
    }
  }

  export function updateDirty<T extends DirtyType>(
    entity: T,
    updatedIds: string[]
  ) {
    entity.dirtyEntities = difference(entity.dirtyEntities, updatedIds);
    if (entity.dirtyEntities.length > 0) {
      entity.state = "dirty";
    } else {
      entity.state = "succeeded";
    }
  }

  export function removeDirty<T extends DirtyType>(
    entity: T,
    removedIds: string[]
  ) {
    entity.dirtyEntities = difference(entity.dirtyEntities, removedIds);
    if (entity.dirtyEntities.length === 0 && entity.state === "dirty") {
      entity.state = "succeeded";
    }
  }
}
