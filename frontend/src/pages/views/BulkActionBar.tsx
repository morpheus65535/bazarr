import { useCallback, useMemo } from "react";
import { Anchor, Group, Text, useCombobox } from "@mantine/core";
import { faCheck } from "@fortawesome/free-solid-svg-icons";
import { UseMutationResult } from "@tanstack/react-query";
import { chunk } from "lodash";
import { useIsAnyMutationRunning, useLanguageProfiles } from "@/apis/hooks";
import { GroupedSelector, GroupedSelectorOptions, Toolbox } from "@/components";
import { useSelectorOptions } from "@/utilities";
import { BulkSelection } from "@/utilities/bulkSelection";

interface ControlsProps {
  selection: BulkSelection;
  totalCount: number;
  loadedIds: number[];
  // "this page" (table) or "loaded" (poster, infinite scroll)
  loadedLabel: string;
  onSelectAllMatching: () => void;
  isSelectingAllMatching: boolean;
}

export const BulkActionBarControls = (props: ControlsProps) => {
  const {
    selection,
    totalCount,
    loadedIds,
    loadedLabel,
    onSelectAllMatching,
    isSelectingAllMatching,
  } = props;

  const { selectedIds, dirties } = selection;

  const { data: profiles } = useLanguageProfiles();
  const profileOptions = useSelectorOptions(profiles ?? [], (v) => v.name);

  const profileOptionsWithAction = useMemo<GroupedSelectorOptions<string>[]>(
    () => [
      {
        group: "Actions",
        items: [{ label: "Clear", value: "", profileId: null }],
      },
      {
        group: "Profiles",
        items: profileOptions.options.map((a) => ({
          value: a.value.profileId.toString(),
          label: a.label,
          profileId: a.value.profileId,
        })),
      },
    ],
    [profileOptions.options],
  );

  const combobox = useCombobox();

  return (
    <Group gap="sm" wrap="wrap" align="center">
      <Text size="sm">
        {selectedIds.size} selected
        {dirties.size > 0 && ` · ${dirties.size} pending`}
        {loadedIds.length > 0 && (
          <>
            {" · "}
            <Anchor
              component="button"
              type="button"
              size="sm"
              underline="hover"
              onClick={() => selection.setMany(loadedIds, true)}
            >
              {`Select all ${loadedIds.length} ${loadedLabel}`}
            </Anchor>
          </>
        )}
        {selectedIds.size < totalCount &&
          (isSelectingAllMatching ? (
            " · Selecting all matching filters…"
          ) : (
            <>
              {" · "}
              <Anchor
                component="button"
                type="button"
                size="sm"
                underline="hover"
                onClick={onSelectAllMatching}
              >
                {`Select all ${totalCount} matching filters`}
              </Anchor>
            </>
          ))}
      </Text>

      <GroupedSelector
        onClick={() => combobox.openDropdown()}
        onDropdownClose={() => combobox.resetSelectedOption()}
        placeholder="Change Profile"
        withCheckIcon={false}
        options={profileOptionsWithAction}
        disabled={selectedIds.size === 0}
        comboboxProps={{
          store: combobox,
          onOptionSubmit: (value) => {
            selection.stage(value ? +value : null);
          },
        }}
      ></GroupedSelector>
    </Group>
  );
};

interface SaveButtonProps {
  selection: BulkSelection;
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem>;
}

export const BulkActionBarSaveButton = (props: SaveButtonProps) => {
  const { selection, mutation } = props;
  const { dirties } = selection;

  const hasTask = useIsAnyMutationRunning();
  const { mutateAsync } = mutation;

  // Chunked to avoid oversized payloads for large selections; sequential to
  // avoid unthrottled server load.
  const save = useCallback(async () => {
    const chunkSize = 1000;

    for (const batch of chunk(Array.from(dirties.entries()), chunkSize)) {
      await mutateAsync({
        id: batch.map(([id]) => id),
        profileId: batch.map(([, profileId]) => profileId),
      });
    }
  }, [dirties, mutateAsync]);

  return (
    <Toolbox.MutateButton
      icon={faCheck}
      disabled={dirties.size === 0 || hasTask}
      promise={save}
      onSuccess={selection.deactivate}
    >
      {`Save (${dirties.size})`}
    </Toolbox.MutateButton>
  );
};
