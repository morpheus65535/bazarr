import api from "@/apis/raw";
import { Selector, SelectorOption } from "@/components";
import MutateButton from "@/components/async/MutateButton";
import { useModals, withModal } from "@/modules/modals";
import { BuildKey } from "@/utilities";
import {
  Button,
  Divider,
  Group,
  SimpleGrid,
  Stack,
  Textarea,
} from "@mantine/core";
import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { useMutation } from "react-query";
import { Card, useLatestArray, useUpdateArray } from "../components";
import { notificationsKey } from "../keys";

interface Props {
  selections: readonly Settings.NotificationInfo[];
  payload: Settings.NotificationInfo | null;
}

const NotificationTool: FunctionComponent<Props> = ({
  selections,
  payload,
}) => {
  const options = useMemo<SelectorOption<Settings.NotificationInfo>[]>(
    () =>
      selections
        .filter((v) => !v.enabled)
        .map((v) => ({
          label: v.name,
          value: v,
        })),
    [selections]
  );

  const update = useUpdateArray<Settings.NotificationInfo>(
    notificationsKey,
    "name"
  );

  const modals = useModals();

  const [current, setCurrent] =
    useState<Nullable<Settings.NotificationInfo>>(payload);

  const updateUrl = useCallback((url: string) => {
    setCurrent((current) => {
      if (current) {
        return {
          ...current,
          url,
        };
      } else {
        return current;
      }
    });
  }, []);

  const canSave =
    current !== null && current?.url !== null && current?.url.length !== 0;

  const getLabel = useCallback((v: Settings.NotificationInfo) => v.name, []);

  const test = useMutation((url: string) => api.system.testNotification(url));

  return (
    <Stack>
      <Selector
        disabled={payload !== null}
        options={options}
        value={current}
        onChange={setCurrent}
        getKey={getLabel}
      ></Selector>
      <div hidden={current === null}>
        <Textarea
          minRows={1}
          maxRows={4}
          placeholder="URL"
          value={current?.url ?? ""}
          onChange={(e) => {
            const value = e.currentTarget.value;
            updateUrl(value);
          }}
        ></Textarea>
      </div>
      <Divider></Divider>
      <Group>
        <MutateButton
          disabled={!canSave}
          mutation={test}
          args={() => current?.url ?? null}
        >
          Test
        </MutateButton>
        <Button
          hidden={payload === null}
          color="danger"
          onClick={() => {
            if (current) {
              update({ ...current, enabled: false });
            }
            modals.closeAll();
          }}
        >
          Remove
        </Button>
        <Button
          disabled={!canSave}
          onClick={() => {
            if (current) {
              update({ ...current, enabled: true });
            }
            modals.closeAll();
          }}
        >
          Save
        </Button>
      </Group>
    </Stack>
  );
};

const NotificationModal = withModal(NotificationTool, "notification-tool", {
  title: "Notification",
});

export const NotificationView: FunctionComponent = () => {
  const notifications = useLatestArray<Settings.NotificationInfo>(
    notificationsKey,
    "name",
    (s) => s.notifications.providers
  );

  const modals = useModals();

  const elements = useMemo(() => {
    return notifications
      ?.filter((v) => v.enabled)
      .map((v, idx) => (
        <Card
          key={BuildKey(idx, v.name)}
          header={v.name}
          onClick={() =>
            modals.openContextModal(NotificationModal, {
              payload: v,
              selections: notifications,
            })
          }
        ></Card>
      ));
  }, [modals, notifications]);

  return (
    <SimpleGrid cols={3}>
      {elements}
      <Card
        plus
        onClick={() =>
          modals.openContextModal(NotificationModal, {
            payload: null,
            selections: notifications ?? [],
          })
        }
      ></Card>
    </SimpleGrid>
  );
};
