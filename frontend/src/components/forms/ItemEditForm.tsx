import { FunctionComponent, useMemo } from "react";
import { Button, Divider, Group, LoadingOverlay, Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import { UseMutationResult } from "@tanstack/react-query";
import { useLanguageProfiles } from "@/apis/hooks";
import { MultiSelector, Selector } from "@/components/inputs";
import { useModals, withModal } from "@/modules/modals";
import { GetItemId, useSelectorOptions } from "@/utilities";

interface Props {
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem, unknown>;
  item: Item.Base | null;
  onComplete?: () => void;
  onCancel?: () => void;
}

const ItemEditForm: FunctionComponent<Props> = ({
  mutation,
  item,
  onComplete,
  onCancel,
}) => {
  const { data, isFetching } = useLanguageProfiles();
  const { isPending, mutate } = mutation;
  const modals = useModals();

  const profileOptions = useSelectorOptions(
    data ?? [],
    (v) => v.name ?? "Unknown",
    (v) => v.profileId.toString() ?? "-1",
  );

  const profile = useMemo(
    () => data?.find((v) => v.profileId === item?.profileId) ?? null,
    [data, item?.profileId],
  );

  const form = useForm({
    initialValues: {
      profile: profile ?? null,
    },
  });

  const options = useSelectorOptions(
    item?.audio_language ?? [],
    (v) => v.name,
    (v) => v.code2 ?? "",
  );

  const isOverlayVisible = isPending || isFetching || item === null;

  return (
    <form
      onSubmit={form.onSubmit(({ profile }) => {
        if (item) {
          const itemId = GetItemId(item);
          if (itemId) {
            mutate({ id: [itemId], profileid: [profile?.profileId ?? null] });
            onComplete?.();
            modals.closeSelf();
            return;
          }
        }

        form.setErrors({ profile: "Invalid profile" });
      })}
    >
      <LoadingOverlay visible={isOverlayVisible}></LoadingOverlay>
      <Stack>
        <MultiSelector
          label="Audio Languages"
          disabled
          {...options}
          value={item?.audio_language ?? []}
        ></MultiSelector>
        <Selector
          {...profileOptions}
          {...form.getInputProps("profile")}
          clearable
          label="Languages Profile"
        ></Selector>
        <Divider></Divider>
        <Group justify="right">
          <Button
            disabled={isOverlayVisible}
            onClick={() => {
              onCancel?.();
              modals.closeSelf();
            }}
            color="gray"
            variant="subtle"
          >
            Cancel
          </Button>
          <Button disabled={isOverlayVisible} type="submit">
            Save
          </Button>
        </Group>
      </Stack>
    </form>
  );
};

export const ItemEditModal = withModal(ItemEditForm, "item-editor", {
  title: "Editor",
  size: "md",
});

export default ItemEditForm;
