import { useEffect } from "react";

export function useAutoUpdate(item: Async.Item<any>, update: () => void) {
  useEffect(() => {
    if (item.state === "uninitialized" || item.state === "dirty") {
      update();
    }
  }, [item.state, update]);
}

export function useAutoListUpdate(
  list: Async.List<any>,
  update: () => void,
  updateIds: (params: number[]) => void
) {
  useEffect(() => {
    if (list.state === "uninitialized") {
      update();
    } else if (list.state === "dirty") {
      updateIds(list.dirtyEntities.map(Number));
    }
  }, [list.state, list.dirtyEntities, updateIds, update]);
}
