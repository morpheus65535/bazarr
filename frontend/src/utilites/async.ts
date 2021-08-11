import { difference, intersection, isString } from "lodash";
import { useEffect, useMemo, useState } from "react";
import { useEffectOnceWhen } from "rooks";
import { useEntityIdByRange, useEntityToItem } from "./entity";

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
  const { content, dirtyEntities, error, state } = entity;
  const item = useEntityToItem(content, id);

  const newState = useMemo<Async.State>(() => {
    if (state === "loading" || state === "uninitialized") {
      return state;
    } else if (dirtyEntities.find((v) => v === id)) {
      return "dirty";
    } else {
      return "succeeded";
    }
  }, [dirtyEntities, id, state]);

  return useMemo(
    () => ({ content: item, state: newState, error }),
    [error, newState, item]
  );
}

// export function useListItemById<T>(
//   list: Async.List<T>,
//   id: string
// ): Async.Item<T> {
//   const { content, dirtyEntities, error, state, keyName } = list;
//   const item = useMemo(
//     () => content.find((v) => String(v[keyName]) === id) ?? null,
//     [content, id, keyName]
//   );

//   const newState = useMemo<Async.State>(() => {
//     if (state === "loading" || state === "uninitialized") {
//       return state;
//     } else if (dirtyEntities.find((v) => v === id)) {
//       return "dirty";
//     } else {
//       return "succeeded";
//     }
//   }, [dirtyEntities, error, id, state]);

//   return useMemo(
//     () => ({ content: item, state: newState, error }),
//     [item, newState, error]
//   );
// }

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
