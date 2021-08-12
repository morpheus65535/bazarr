import { useEffect } from "react";
import { log } from "../../utilites/logger";

export function useAutoUpdate(item: Async.Item<any>, update: () => void) {
  useEffect(() => {
    if (item.state === "uninitialized" || item.state === "dirty") {
      update();
    }
  }, [item.state, update]);
}

export function useAutoDirtyUpdate(
  item: Async.List<any> | Async.Entity<any>,
  update: (ids: number[]) => void
) {
  const { state, dirtyEntities } = item;
  const hasDirty = dirtyEntities.length > 0 && state === "dirty";

  useEffect(() => {
    if (hasDirty) {
      log("info", "updating dirty entities...");
      update(dirtyEntities.map(Number));
    }
  }, [hasDirty, dirtyEntities, update]);
}
