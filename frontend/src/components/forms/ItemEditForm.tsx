import { useLanguageProfiles } from "@/apis/hooks";
import { Selector } from "@/components/inputs";
import { BuildKey, GetItemId, useSelectorOptions } from "@/utilities";
import {
  Badge,
  Button,
  Divider,
  Group,
  LoadingOverlay,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";
import { useForm } from "@mantine/hooks";
import { FunctionComponent } from "react";
import { UseMutationResult } from "react-query";

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
  const { isLoading, mutate } = mutation;

  const profileOptions = useSelectorOptions(
    data ?? [],
    (v) => v.name ?? "Unknown"
  );

  const form = useForm({
    initialValues: {
      profileId: item?.profileId ?? null,
    },
  });

  const isOverlayVisible = isLoading || isFetching || item === null;

  return (
    <form
      onSubmit={form.onSubmit(({ profileId }) => {
        if (item) {
          const itemId = GetItemId(item);
          if (itemId) {
            mutate({ id: [itemId], profileid: [profileId] });
            return;
          }
        }

        form.setErrors({ profileId: "Invalid profile" });
      })}
    >
      <LoadingOverlay visible={isOverlayVisible}></LoadingOverlay>
      <Stack>
        <div>
          <Text size="sm" weight="normal" mb="xs">
            Audio Languages
          </Text>
          <SimpleGrid>
            {item?.audio_language.map((v, i) => (
              <Badge key={BuildKey(v, i)}>{v.name}</Badge>
            ))}
          </SimpleGrid>
        </div>
        <Selector
          {...profileOptions}
          {...form.getInputProps("profileId")}
          label="Languages Profiles"
        ></Selector>
        <Divider></Divider>
        <Group position="apart">
          <Button
            disabled={isOverlayVisible}
            onClick={onCancel}
            color="gray"
            variant="subtle"
          >
            Cancel
          </Button>
          <Button disabled={isOverlayVisible} uppercase type="submit">
            Submit
          </Button>
        </Group>
      </Stack>
    </form>
  );
};

export default ItemEditForm;
