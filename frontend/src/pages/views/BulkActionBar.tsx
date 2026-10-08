import { useCallback, useMemo, useState } from "react";
import { Button, Group, Text, useCombobox } from "@mantine/core";
import { faCheck, faSearch } from "@fortawesome/free-solid-svg-icons";
import { UseMutationResult } from "@tanstack/react-query";
import { chunk } from "lodash";
import { useIsAnyMutationRunning, useLanguageProfiles } from "@/apis/hooks";
import { GroupedSelector, GroupedSelectorOptions, Toolbox } from "@/components";
import { useSelectorOptions } from "@/utilities";
import { BulkSelection } from "@/utilities/bulkSelection";
import SearchMissingModal, { SearchMissingConfig } from "./SearchMissingModal";
import ToolboxIconButton from "./ToolboxIconButton";

// Module-scoped so useSelectorOptions stays referentially stable across
// renders (this component re-renders on every selection change).
const profileName = (v: Language.Profile) => v.name;

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
  const profileOptions = useSelectorOptions(profiles ?? [], profileName);

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
      </Text>
      {loadedIds.length > 0 && (
        <Button
          variant="outline"
          color="gray"
          size="xs"
          onClick={() => selection.setMany(loadedIds, true)}
        >
          {`Select all ${loadedIds.length} ${loadedLabel}`}
        </Button>
      )}
      {selectedIds.size < totalCount &&
        (isSelectingAllMatching ? (
          <Text size="sm" c="dimmed">
            Selecting all matching filters…
          </Text>
        ) : (
          <Button
            variant="outline"
            color="gray"
            size="xs"
            onClick={onSelectAllMatching}
          >
            {`Select all ${totalCount} matching filters`}
          </Button>
        ))}

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

interface SearchButtonProps {
  selection: BulkSelection;
  config: SearchMissingConfig;
}

// Searches for missing subtitles for the selected items. Disabled until at
// least one item is selected.
export const BulkActionBarSearchButton = (props: SearchButtonProps) => {
  const { selection, config } = props;
  const [opened, setOpened] = useState(false);

  const ids = useMemo(
    () => Array.from(selection.selectedIds),
    [selection.selectedIds],
  );

  return (
    <>
      <ToolboxIconButton
        icon={faSearch}
        disabled={ids.length === 0}
        onClick={() => setOpened(true)}
      >
        {`Search Selected (${ids.length})`}
      </ToolboxIconButton>
      <SearchMissingModal
        opened={opened}
        onClose={() => setOpened(false)}
        ids={ids}
        config={config}
      ></SearchMissingModal>
    </>
  );
};
