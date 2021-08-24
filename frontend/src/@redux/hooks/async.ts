import { AsyncThunk } from "@reduxjs/toolkit";
import { useEffect } from "react";
import { log } from "../../utilities/logger";
import { useReduxAction } from "./base";

export function useAutoUpdate(item: Async.Item<any>, update: () => void) {
  useEffect(() => {
    if (item.state === "uninitialized" || item.state === "dirty") {
      update();
    }
  }, [item.state, update]);
}

export function useAutoDirtyUpdate(
  item: Async.List<any> | Async.Entity<any>,
  updateAction: AsyncThunk<any, number[], {}>
) {
  const { state, dirtyEntities } = item;
  const hasDirty = dirtyEntities.length > 0 && state === "dirty";

  const update = useReduxAction(updateAction);

  useEffect(() => {
    if (hasDirty) {
      log("info", "updating dirty entities...");
      update(dirtyEntities.map(Number));
    }
  }, [hasDirty, dirtyEntities, update]);
}
