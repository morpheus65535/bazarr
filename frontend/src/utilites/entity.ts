import { isString } from "lodash";
import { useMemo } from "react";

export function useEntityIdByRange(
  entity: EntityStruct<any>,
  start: number,
  end: number
) {
  return useMemo<[string[], boolean]>(() => {
    const ids = entity.ids;
    let hasEmpty = false;
    return [
      ids.slice(start, end).flatMap((v) => {
        if (isString(v)) {
          return [v];
        } else {
          hasEmpty = true;
          return [];
        }
      }),
      hasEmpty,
    ];
  }, [entity.ids, start, end]);
}

export function useEntityContentByRange<T>(
  entity: EntityStruct<T>,
  start: number,
  end: number
): [T[], boolean] {
  const [filteredIds, hasEmpty] = useEntityIdByRange(entity, start, end);
  const content = useMemo<T[]>(() => {
    const entities = entity.entities;
    return filteredIds.map((v) => entities[v]);
  }, [entity.entities, filteredIds]);
  return [content, hasEmpty];
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
