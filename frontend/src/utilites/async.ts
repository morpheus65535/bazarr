import { difference, intersection, isString } from "lodash";
import { useEffect, useMemo, useState } from "react";
import { useEffectOnceWhen } from "rooks";
import { useEntityIdByRange, useEntityToItem } from "./entity";

export async function waitFor(time: number) {
  return new Promise((resolved) => {
    setTimeout(resolved, time);
  });
}

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

export function useEntityItemById<T>(
  entity: Async.Entity<T>,
  id: string
): Async.Item<T> {
  const { content, dirtyEntities, didLoaded, error, state } = entity;
  const item = useEntityToItem(content, id);

  const newState = useMemo<Async.State>(() => {
    switch (state) {
      case "loading":
        return state;
      default:
        if (dirtyEntities.find((v) => v === id)) {
          return "dirty";
        } else if (!didLoaded.find((v) => v === id)) {
          return "uninitialized";
        } else {
          return state;
        }
    }
  }, [dirtyEntities, id, state, didLoaded]);

  return useMemo(
    () => ({ content: item, state: newState, error }),
    [error, newState, item]
  );
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
