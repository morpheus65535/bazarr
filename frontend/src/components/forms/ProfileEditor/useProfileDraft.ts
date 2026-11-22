import { useCallback, useMemo, useState } from "react";
import { isEqual } from "lodash";
import {
  collectGroupItems,
  createProfileItem,
  nextGroupId,
  nextItemId,
} from "@/pages/Settings/Languages/profileModel";
import { ProfileDraft, toProfileDraft } from "./profileDraft";

export interface ProfileDraftController {
  draft: ProfileDraft;
  isDirty: boolean;
  cutoffResetNotice: string | null;
  setName: (name: string) => void;
  setTag: (tag: string | undefined) => void;
  setCutoff: (cutoff: number | null) => void;
  setOriginalFormat: (isOriginalFormat: boolean) => void;
  setMustContain: (values: string[]) => void;
  setMustNotContain: (values: string[]) => void;
  addGroup: () => void;
  removeGroup: (groupId: number) => void;
  moveGroup: (groupId: number, direction: -1 | 1) => void;
  setGroupOperator: (
    groupId: number,
    operator: Language.EnhancedGroup["operator"],
  ) => void;
  addItem: (groupId: number) => void;
  updateItem: (
    groupId: number,
    itemId: number,
    patch: Partial<Language.ProfileItem>,
  ) => void;
  removeItem: (groupId: number, itemId: number) => void;
  dismissCutoffResetNotice: () => void;
}

const cutoffRemovedNotice =
  "The stopping rule was reset because its requirement was removed.";

export const useProfileDraft = (
  profile: Language.Profile,
): ProfileDraftController => {
  const [baseline] = useState<ProfileDraft>(() => toProfileDraft(profile));
  const [draft, setDraft] = useState<ProfileDraft>(() =>
    toProfileDraft(profile),
  );
  const [cutoffResetNotice, setCutoffResetNotice] = useState<string | null>(
    null,
  );

  const isDirty = useMemo(() => !isEqual(draft, baseline), [draft, baseline]);

  const updateDraft = useCallback(
    (updater: (current: ProfileDraft) => ProfileDraft) => {
      setDraft(updater);
    },
    [],
  );

  const updateGroups = useCallback(
    (
      updater: (groups: Language.EnhancedGroup[]) => Language.EnhancedGroup[],
    ) => {
      setDraft((current) => ({ ...current, groups: updater(current.groups) }));
    },
    [],
  );

  const setName = useCallback(
    (name: string) => updateDraft((current) => ({ ...current, name })),
    [updateDraft],
  );

  const setTag = useCallback(
    (tag: string | undefined) =>
      updateDraft((current) => ({ ...current, tag })),
    [updateDraft],
  );

  const setCutoff = useCallback(
    (cutoff: number | null) =>
      updateDraft((current) => ({ ...current, cutoff })),
    [updateDraft],
  );

  const setOriginalFormat = useCallback(
    (isOriginalFormat: boolean) =>
      updateDraft((current) => ({
        ...current,
        originalFormat: isOriginalFormat,
      })),
    [updateDraft],
  );

  const setMustContain = useCallback(
    (mustContain: string[]) =>
      updateDraft((current) => ({ ...current, mustContain })),
    [updateDraft],
  );

  const setMustNotContain = useCallback(
    (mustNotContain: string[]) =>
      updateDraft((current) => ({ ...current, mustNotContain })),
    [updateDraft],
  );

  const addGroup = useCallback(() => {
    updateDraft((current) => {
      const itemId = nextItemId(collectGroupItems(current.groups));

      return {
        ...current,
        groups: [
          ...current.groups,
          {
            id: nextGroupId(current.groups),
            operator: "AND",
            items: [createProfileItem(itemId, "")],
          },
        ],
      };
    });
  }, [updateDraft]);

  const removeGroup = useCallback(
    (groupId: number) => {
      if (draft.cutoff === groupId) {
        setCutoffResetNotice(cutoffRemovedNotice);
      }

      updateDraft((current) => ({
        ...current,
        cutoff: current.cutoff === groupId ? null : current.cutoff,
        groups: current.groups.filter((group) => group.id !== groupId),
      }));
    },
    [draft.cutoff, updateDraft],
  );

  const moveGroup = useCallback(
    (groupId: number, direction: -1 | 1) => {
      updateGroups((groups) => {
        const index = groups.findIndex((group) => group.id === groupId);
        const target = index + direction;

        if (index === -1 || target < 0 || target >= groups.length) {
          return groups;
        }

        const reordered = [...groups];
        [reordered[index], reordered[target]] = [
          reordered[target],
          reordered[index],
        ];
        return reordered;
      });
    },
    [updateGroups],
  );

  const setGroupOperator = useCallback(
    (groupId: number, operator: Language.EnhancedGroup["operator"]) => {
      updateGroups((groups) =>
        groups.map((group) =>
          group.id === groupId ? { ...group, operator } : group,
        ),
      );
    },
    [updateGroups],
  );

  const addItem = useCallback(
    (groupId: number) => {
      updateDraft((current) => {
        const itemId = nextItemId(collectGroupItems(current.groups));

        return {
          ...current,
          groups: current.groups.map((group) =>
            group.id === groupId
              ? {
                  ...group,
                  items: [...group.items, createProfileItem(itemId, "")],
                }
              : group,
          ),
        };
      });
    },
    [updateDraft],
  );

  const updateItem = useCallback(
    (groupId: number, itemId: number, patch: Partial<Language.ProfileItem>) => {
      updateGroups((groups) =>
        groups.map((group) =>
          group.id === groupId
            ? {
                ...group,
                items: group.items.map((item) =>
                  item.id === itemId ? { ...item, ...patch } : item,
                ),
              }
            : group,
        ),
      );
    },
    [updateGroups],
  );

  const removeItem = useCallback(
    (groupId: number, itemId: number) => {
      if (draft.cutoff === itemId) {
        setCutoffResetNotice(cutoffRemovedNotice);
      }

      updateDraft((current) => ({
        ...current,
        cutoff: current.cutoff === itemId ? null : current.cutoff,
        groups: current.groups.map((group) =>
          group.id === groupId
            ? {
                ...group,
                items: group.items.filter((item) => item.id !== itemId),
              }
            : group,
        ),
      }));
    },
    [draft.cutoff, updateDraft],
  );

  const dismissCutoffResetNotice = useCallback(
    () => setCutoffResetNotice(null),
    [],
  );

  return useMemo(
    () => ({
      draft,
      isDirty,
      cutoffResetNotice,
      setName,
      setTag,
      setCutoff,
      setOriginalFormat,
      setMustContain,
      setMustNotContain,
      addGroup,
      removeGroup,
      moveGroup,
      setGroupOperator,
      addItem,
      updateItem,
      removeItem,
      dismissCutoffResetNotice,
    }),
    [
      draft,
      isDirty,
      cutoffResetNotice,
      setName,
      setTag,
      setCutoff,
      setOriginalFormat,
      setMustContain,
      setMustNotContain,
      addGroup,
      removeGroup,
      moveGroup,
      setGroupOperator,
      addItem,
      updateItem,
      removeItem,
      dismissCutoffResetNotice,
    ],
  );
};
