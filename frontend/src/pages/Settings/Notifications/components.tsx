import { FunctionComponent, useCallback, useMemo } from "react";
import {
  Button,
  Divider,
  Group,
  SimpleGrid,
  Stack,
  Textarea,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation } from "@tanstack/react-query";
import { isObject } from "lodash";
import api from "@/apis/raw";
import { Selector } from "@/components";
import MutateButton from "@/components/async/MutateButton";
import { useModals, withModal } from "@/modules/modals";
import { Card } from "@/pages/Settings/components";
import { notificationsKey } from "@/pages/Settings/keys";
import {
  useSettingValue,
  useUpdateArray,
} from "@/pages/Settings/utilities/hooks";
import { BuildKey, useSelectorOptions } from "@/utilities";
import FormUtils from "@/utilities/form";

const notificationHook = (notifications: Settings.NotificationInfo[]) => {
  return notifications.map((info) => JSON.stringify(info));
};

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
    [payload?.name, selections],
  );
  const options = useSelectorOptions(availableSelections, (v) => v.name);

  const modals = useModals();

  const form = useForm({
    initialValues: {
      selection: payload,
      url: payload?.url ?? "",
    },
    validate: {
      selection: FormUtils.validation(
        isObject,
        "Please select a notification provider",
      ),
      url: FormUtils.validation(
        (value: string) => value.trim().length !== 0,
        "URL must not be empty",
      ),
    },
  });

  const test = useMutation({
    mutationFn: (url: string) => api.system.testNotification(url),
  });

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
          searchable
          disabled={payload !== null}
          {...options}
          {...form.getInputProps("selection")}
          // We also to update the url, so override the default event from getInputProps
          onChange={(value) => {
            form.setValues({ selection: value, url: value?.url ?? undefined });
          }}
        ></Selector>
        <div hidden={form.values.selection === null}>
          <Textarea
            minRows={4}
            placeholder="URL"
            {...form.getInputProps("url")}
          ></Textarea>
        </div>
        <Divider></Divider>
        <Group justify="right">
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
  const notifications = useSettingValue<Settings.NotificationInfo[]>(
    notificationsKey,
    {
      onLoaded: (settings) => settings.notifications.providers,
      onSubmit: (value) => value.map((v) => JSON.stringify(v)),
    },
  );

  const update = useUpdateArray<Settings.NotificationInfo>(
    notificationsKey,
    notifications ?? [],
    "name",
  );

  const updateWrapper = useCallback(
    (info: Settings.NotificationInfo) => {
      update(info, notificationHook);
    },
    [update],
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
              onComplete: updateWrapper,
            })
          }
        ></Card>
      ));
  }, [modals, notifications, updateWrapper]);

  return (
    <SimpleGrid cols={3}>
      {elements}
      <Card
        plus
        onClick={() =>
          modals.openContextModal(NotificationModal, {
            payload: null,
            selections: notifications ?? [],
            onComplete: updateWrapper,
          })
        }
      ></Card>
    </SimpleGrid>
  );
};
