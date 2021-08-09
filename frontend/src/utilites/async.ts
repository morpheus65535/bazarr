import { intersection } from "lodash";
import { useMemo } from "react";
import { useEntityIdByRange } from "./entity";

export function useIsDirtyEntityInRange<T>(
  entity: Async.Entity<T>,
  start: number,
  end: number
): boolean {
  const [ids] = useEntityIdByRange(entity.content, start, end);

  return useMemo<boolean>(() => {
    const dirtyIds = entity.dirtyEntities;
    return intersection(ids, dirtyIds).length > 0;
  }, [ids, entity.dirtyEntities]);
}
