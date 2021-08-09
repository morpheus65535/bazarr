import { difference, intersection, isString } from "lodash";
import { useEffect, useMemo, useState } from "react";
import { useEffectOnceWhen } from "rooks";
import {
  useEntityByRange,
  useEntityIdByRange,
  useIsEntityIncomplete,
} from "./entity";

export function useHasNewEntity(entity: Async.Entity<any>): boolean {
  return useMemo<boolean>(() => {
    const dirtyEntities = entity.dirtyEntities;
    const rawIds = entity.content.ids;

    const ids = rawIds.filter(isString);
    const diff = difference(dirtyEntities, ids);

    return diff.length > 0 && entity.state === "dirty";
  }, [entity.dirtyEntities, entity.content.ids, entity.state]);
}

export function useHasDirtyEntity(
  entity: Async.Entity<any>,
  start: number,
  end: number
): boolean {
  const ids = useEntityIdByRange(entity.content, start, end);

  const hasDirty = useMemo<boolean>(() => {
    const dirtyIds = entity.dirtyEntities;
    return intersection(ids, dirtyIds).length > 0;
  }, [ids, entity.dirtyEntities]);

  return hasDirty;
}

export function useEntityPagination<T>(
  entity: Async.Entity<T>,
  loader: (range: Parameter.Range) => void,
  start: number,
  end: number
): T[] {
  const { state, content } = entity;

  const [hasLoaded, setHasLoaded] = useState(false);

  useEffect(() => {
    setHasLoaded(false);
  }, [start, end]);

  const needInit = state === "uninitialized";
  const hasNew = useHasNewEntity(entity) && !hasLoaded;
  const hasEmpty = useIsEntityIncomplete(content, start, end);
  const hasDirty = useHasDirtyEntity(entity, start, end) && state === "dirty";

  useEffect(() => {
    if (needInit || hasEmpty || hasNew || hasDirty) {
      const length = end - start;
      loader({ start, length });
      if (hasNew) {
        setHasLoaded(true);
      }
    }
  }, [start, end, needInit, hasDirty, hasEmpty, hasNew, loader]);

  return useEntityByRange(content, start, end);
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
