import api from "@/apis/raw";
import { Selector, SelectorOption } from "@/components";
import { AsyncButton } from "@/components/async";
import {
  useModal,
  useModalControl,
  usePayload,
  withModal,
} from "@/modules/modals";
import { BuildKey } from "@/utilities";
import { Button, Container, Grid, Stack, Textarea } from "@mantine/core";
import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { ColCard, useLatestArray, useUpdateArray } from "../components";
import { notificationsKey } from "../keys";

interface Props {
  selections: readonly Settings.NotificationInfo[];
}

const NotificationTool: FunctionComponent<Props> = ({ selections }) => {
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

  const payload = usePayload<Settings.NotificationInfo>();

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

  const Modal = useModal({
    onMounted: () => {
      setCurrent(payload);
    },
  });

  const { hide } = useModalControl();

  const footer = (
    <>
      <AsyncButton
        disabled={!canSave}
        promise={() => {
          if (current && current.url) {
            return api.system.testNotification(current.url);
          } else {
            return null;
          }
        }}
      >
        Test
      </AsyncButton>
      <Button
        hidden={payload === null}
        color="danger"
        onClick={() => {
          if (current) {
            update({ ...current, enabled: false });
          }
          hide();
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
          hide();
        }}
      >
        Save
      </Button>
    </>
  );

  return (
    <Modal title="Notification" footer={footer}>
      <Stack>
        <Selector
          disabled={payload !== null}
          options={options}
          value={current}
          onChange={setCurrent}
          label={getLabel}
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
      </Stack>
    </Modal>
  );
};

const NotificationModal = withModal(NotificationTool, "notification-tool");

export const NotificationView: FunctionComponent = () => {
  const notifications = useLatestArray<Settings.NotificationInfo>(
    notificationsKey,
    "name",
    (s) => s.notifications.providers
  );

  const { show } = useModalControl();

  const elements = useMemo(() => {
    return notifications
      ?.filter((v) => v.enabled)
      .map((v, idx) => (
        <Grid.Col key={BuildKey(idx, v.name)}>
          <ColCard
            header={v.name}
            onClick={() => show(NotificationModal, v)}
          ></ColCard>
        </Grid.Col>
      ));
  }, [notifications, show]);

  return (
    <Container fluid>
      <Grid>
        {elements}
        <Grid.Col>
          <ColCard plus onClick={() => show(NotificationModal)}></ColCard>
        </Grid.Col>
      </Grid>
      <NotificationModal selections={notifications ?? []}></NotificationModal>
    </Container>
  );
};
