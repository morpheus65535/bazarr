import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Button, Col, Container, Form, Row } from "react-bootstrap";
import { SystemApi } from "../../apis";
import {
  AsyncButton,
  BaseModal,
  BaseModalProps,
  Selector,
  useModalInformation,
  useOnModalShow,
  useShowModal,
} from "../../components";
import { BuildKey } from "../../utilities";
import { ColCard, useLatestArray, useUpdateArray } from "../components";
import { notificationsKey } from "../keys";

interface ModalProps {
  selections: readonly Settings.NotificationInfo[];
}

const NotificationModal: FunctionComponent<ModalProps & BaseModalProps> = ({
  selections,
  ...modal
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

  const { payload, closeModal } =
    useModalInformation<Settings.NotificationInfo>(modal.modalKey);

  const [current, setCurrent] =
    useState<Nullable<Settings.NotificationInfo>>(payload);

  useOnModalShow<Settings.NotificationInfo>(
    (p) => setCurrent(p),
    modal.modalKey
  );

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

  const footer = useMemo(
    () => (
      <React.Fragment>
        <AsyncButton
          className="mr-auto"
          disabled={!canSave}
          variant="outline-secondary"
          promise={() => {
            if (current && current.url) {
              return SystemApi.testNotification(current.url);
            } else {
              return null;
            }
          }}
        >
          Test
        </AsyncButton>
        <Button
          hidden={payload === null}
          variant="danger"
          onClick={() => {
            if (current) {
              update({ ...current, enabled: false });
            }
            closeModal();
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
            closeModal();
          }}
        >
          Save
        </Button>
      </React.Fragment>
    ),
    [canSave, closeModal, current, update, payload]
  );

  const getLabel = useCallback((v: Settings.NotificationInfo) => v.name, []);

  return (
    <BaseModal title="Notification" footer={footer} {...modal}>
      <Container fluid>
        <Row>
          <Col xs={12}>
            <Selector
              disabled={payload !== null}
              options={options}
              value={current}
              onChange={setCurrent}
              label={getLabel}
            ></Selector>
          </Col>
          <Col hidden={current === null}>
            <Form.Group className="mt-4">
              <Form.Control
                as="textarea"
                rows={4}
                placeholder="URL"
                value={current?.url ?? ""}
                onChange={(e) => {
                  const value = e.currentTarget.value;
                  updateUrl(value);
                }}
              ></Form.Control>
            </Form.Group>
          </Col>
        </Row>
      </Container>
    </BaseModal>
  );
};

export const NotificationView: FunctionComponent = () => {
  const notifications = useLatestArray<Settings.NotificationInfo>(
    notificationsKey,
    "name",
    (s) => s.notifications.providers
  );

  const showModal = useShowModal();

  const elements = useMemo(() => {
    return notifications
      ?.filter((v) => v.enabled)
      .map((v, idx) => (
        <ColCard
          key={BuildKey(idx, v.name)}
          header={v.name}
          onClick={() => showModal("notifications", v)}
        ></ColCard>
      ));
  }, [notifications, showModal]);

  return (
    <Container fluid>
      <Row>
        {elements}{" "}
        <ColCard plus onClick={() => showModal("notifications")}></ColCard>
      </Row>
      <NotificationModal
        selections={notifications ?? []}
        modalKey="notifications"
      ></NotificationModal>
    </Container>
  );
};
