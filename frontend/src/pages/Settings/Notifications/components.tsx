import api from "@/apis/raw";
import { Selector } from "@/components";
import MutateButton from "@/components/async/MutateButton";
import { useModals, withModal } from "@/modules/modals";
import { BuildKey, useSelectorOptions } from "@/utilities";
import {
  Button,
  Divider,
  Group,
  SimpleGrid,
  Stack,
  Textarea,
} from "@mantine/core";
import { useForm } from "@mantine/hooks";
import { FunctionComponent, useMemo } from "react";
import { useMutation } from "react-query";
import { Card, useLatestArray, useUpdateArray } from "../components";
import { notificationsKey } from "../keys";

interface Props {
  selections: readonly Settings.NotificationInfo[];
  payload: Settings.NotificationInfo | null;
  onComplete: (info: Settings.NotificationInfo) => void;
}

const NotificationForm: FunctionComponent<Props> = ({
  selections,
  payload,
  onComplete,
}) => {
  const availableSelections = useMemo(
    () => selections.filter((v) => !v.enabled || v.name === payload?.name),
    [payload?.name, selections]
  );
  const options = useSelectorOptions(availableSelections, (v) => v.name);

  const modals = useModals();

  const form = useForm({
    initialValues: {
      selection: payload,
      url: payload?.url ?? "",
    },
    validationRules: {
      selection: (value) => value !== null,
      url: (value) => value.trim() !== "",
    },
  });

  const test = useMutation((url: string) => api.system.testNotification(url));

  return (
    <form
      onSubmit={form.onSubmit(({ selection, url }) => {
        if (selection) {
          onComplete({ ...selection, enabled: true, url });
        }
        modals.closeSelf();
      })}
    >
      <Stack>
        <Selector
          disabled={payload !== null}
          {...options}
          {...form.getInputProps("selection")}
        ></Selector>
        <div hidden={form.values.selection === null}>
          <Textarea
            minRows={4}
            placeholder="URL"
            {...form.getInputProps("url")}
          ></Textarea>
        </div>
        <Divider></Divider>
        <Group position="right">
          <MutateButton mutation={test} args={() => form.values.url}>
            Test
          </MutateButton>
          <Button
            hidden={payload === null}
            color="red"
            onClick={() => {
              if (payload) {
                onComplete({ ...payload, enabled: false });
              }
              modals.closeAll();
            }}
          >
            Remove
          </Button>
          <Button type="submit">Save</Button>
        </Group>
      </Stack>
    </form>
  );
};

const NotificationModal = withModal(NotificationForm, "notification-tool", {
  title: "Notification",
});

export const NotificationView: FunctionComponent = () => {
  const notifications = useLatestArray<Settings.NotificationInfo>(
    notificationsKey,
    "name",
    (s) => s.notifications.providers
  );

  const update = useUpdateArray<Settings.NotificationInfo>(
    notificationsKey,
    "name"
  );

  const modals = useModals();

  const elements = useMemo(() => {
    return notifications
      ?.filter((v) => v.enabled)
      .map((payload, idx) => (
        <Card
          key={BuildKey(idx, payload.name)}
          header={payload.name}
          onClick={() =>
            modals.openContextModal(NotificationModal, {
              payload,
              selections: notifications,
              onComplete: update,
            })
          }
        ></Card>
      ));
  }, [modals, notifications, update]);

  return (
    <SimpleGrid cols={3}>
      {elements}
      <Card
        plus
        onClick={() =>
          modals.openContextModal(NotificationModal, {
            payload: null,
            selections: notifications ?? [],
            onComplete: update,
          })
        }
      ></Card>
    </SimpleGrid>
  );
};
