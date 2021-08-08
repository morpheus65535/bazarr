import { isString } from "lodash";
import { useMemo } from "react";

export function useEntityIdByRange(
  entity: EntityStruct<any>,
  start: number,
  end: number
) {
  return useMemo<string[]>(() => {
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

export function useEntityContentByRange<T>(
  entity: EntityStruct<T>,
  start: number,
  end: number
): T[] {
  const filteredIds = useEntityIdByRange(entity, start, end);
  return useMemo<T[]>(() => {
    const entities = entity.entities;
    return filteredIds.map((v) => entities[v]);
  }, [entity.entities, filteredIds]);
}

export function useConvertEntityToList<T>(entity: EntityStruct<T>): T[] {
  return useMemo<T[]>(
    () =>
      entity.ids.flatMap((v) => {
        if (v) {
          return [entity.entities[v]];
        } else {
          return [];
        }
      }),
    [entity]
  );
}
