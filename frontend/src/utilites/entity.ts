import { isNull, isString } from "lodash";
import { useMemo } from "react";

export function useIsEntityLoaded(
  entity: EntityStruct<any>,
  start: number,
  end: number
): boolean {
  return useMemo(
    () => entity.ids.slice(start, end).filter(isNull).length === 0,
    [entity.ids, start, end]
  );
}

export function useEntityIdByRange(
  entity: EntityStruct<any>,
  start: number,
  end: number
): string[] {
  return useMemo(() => {
    const ids = entity.ids;
    return ids.slice(start, end).flatMap((v) => {
      if (isString(v)) {
        return [v];
      } else {
        return [];
      }
    });
  }, [entity.ids, start, end]);
}

export function useEntityByRange<T>(
  entity: EntityStruct<T>,
  start: number,
  end: number
): T[] {
  const filteredIds = useEntityIdByRange(entity, start, end);
  const content = useMemo<T[]>(() => {
    const entities = entity.entities;
    return filteredIds.map((v) => entities[v]);
  }, [entity.entities, filteredIds]);
  return content;
}

export function useEntityToList<T>(entity: EntityStruct<T>): T[] {
  return useMemo(
    () => entity.ids.filter(isString).map((v) => entity.entities[v]),
    [entity]
  );
}

export function useEntityToItem<T>(
  entity: EntityStruct<T>,
  id: string
): T | null {
  return useMemo(() => {
    if (id in entity.entities) {
      return entity.entities[id];
    } else {
      return null;
    }
  }, [entity.entities, id]);
}
