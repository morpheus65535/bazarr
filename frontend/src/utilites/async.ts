import { difference, intersection, isString } from "lodash";
import { useEffect, useMemo, useState } from "react";
import { useEffectOnceWhen } from "rooks";
import { useEntityIdByRange } from "./entity";

export function useNewEntityIds(entity: Async.Entity<any>) {
  return useMemo(() => {
    const dirtyEntities = entity.dirtyEntities;
    const rawIds = entity.content.ids;

    const ids = rawIds.filter(isString);

    return difference(dirtyEntities, ids);
  }, [entity.dirtyEntities, entity.content.ids]);
}

export function useDirtyEntityIds(
  entity: Async.Entity<any>,
  start: number,
  end: number
) {
  const ids = useEntityIdByRange(entity.content, start, end);

  return useMemo(() => {
    const dirtyIds = entity.dirtyEntities;
    return intersection(ids, dirtyIds);
  }, [ids, entity.dirtyEntities]);
}

export function useOnLoadedOnce(callback: () => void, entity: Async.Base<any>) {
  const [didLoaded, setLoaded] = useState(false);

  const { state } = entity;

  const isLoaded = state !== "loading";

  useEffect(() => {
    if (!isLoaded) {
      setLoaded(true);
    }
  }, [isLoaded]);

  useEffectOnceWhen(callback, didLoaded && isLoaded);
}
