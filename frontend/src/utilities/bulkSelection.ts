import { useCallback, useMemo, useRef, useState } from "react";
import { useResetOnChange } from "@/utilities/resetOnChange";

export interface BulkSelection {
  active: boolean;
  toggleActive: () => void;
  // Idempotent - safe to call even if already inactive (e.g. a promise
  // callback resolving after the user already cancelled).
  deactivate: () => void;
  selectedIds: ReadonlySet<number>;
  dirties: ReadonlyMap<number, number | null>;
  isSelected: (id: number) => boolean;
  toggle: (id: number) => void;
  setMany: (ids: number[], selected: boolean) => void;
  stage: (profileId: number | null) => void;
  clear: () => void;
}

// resetKey is a filters-only key: a filter change means selectedIds no
// longer matches "select all"; dirties survives since it's filter-independent.
export const useBulkSelection = (resetKey: string): BulkSelection => {
  const [active, setActive] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(() => new Set());
  const [dirties, setDirties] = useState<Map<number, number | null>>(
    () => new Map(),
  );

  useResetOnChange(resetKey, () => setSelectedIds(new Set()));

  const clear = useCallback(() => {
    setSelectedIds(new Set());
    setDirties(new Map());
  }, []);

  // Read via ref (not the closed-over value) so setActive's updater stays
  // pure; safe since toggleActive is only ever a live, synchronous click.
  const activeRef = useRef(active);
  activeRef.current = active;

  const toggleActive = useCallback(() => {
    if (activeRef.current) {
      clear();
    }
    setActive((prev) => !prev);
  }, [clear]);

  const deactivate = useCallback(() => {
    clear();
    setActive(false);
  }, [clear]);

  const isSelected = useCallback(
    (id: number) => selectedIds.has(id),
    [selectedIds],
  );

  const toggle = useCallback((id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const setMany = useCallback((ids: number[], selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => {
        if (selected) {
          next.add(id);
        } else {
          next.delete(id);
        }
      });
      return next;
    });
  }, []);

  const stage = useCallback(
    (profileId: number | null) => {
      setDirties((prev) => {
        const next = new Map(prev);
        selectedIds.forEach((id) => next.set(id, profileId));
        return next;
      });
      setSelectedIds(new Set());
    },
    [selectedIds],
  );

  return useMemo(
    () => ({
      active,
      toggleActive,
      deactivate,
      selectedIds,
      dirties,
      isSelected,
      toggle,
      setMany,
      stage,
      clear,
    }),
    [
      active,
      toggleActive,
      deactivate,
      selectedIds,
      dirties,
      isSelected,
      toggle,
      setMany,
      stage,
      clear,
    ],
  );
};
