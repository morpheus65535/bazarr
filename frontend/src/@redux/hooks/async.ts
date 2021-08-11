import { useEffect } from "react";

export function useAutoUpdate(item: Async.Item<any>, update: () => void) {
  useEffect(() => {
    if (item.state === "uninitialized" || item.state === "dirty") {
      update();
    }
  }, [item.state, update]);
}
