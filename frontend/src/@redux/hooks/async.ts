import { useEffect } from "react";

export function useAutoUpdate(item: Async.Base<any>, updateAll: () => void) {
  useEffect(() => {
    if (item.state === "uninitialized" || item.state === "dirty") {
      updateAll();
    }
  }, [item.state, updateAll]);
}
