import React, { FunctionComponent, useState } from "react";
import { Container, Form } from "react-bootstrap";
import { AsyncButton } from "../";
import { useIsAnyTaskRunningWithId } from "../../@modules/task/hooks";
import { GetItemId } from "../../utilities";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useModalInformation } from "./hooks";

interface Props {
  submit: (form: FormType.FixMatchItem) => Promise<void>;
  onSuccess?: (item: Item.Base) => void;
}

const FixMatch: FunctionComponent<Props & BaseModalProps> = (props) => {
  const { onSuccess, submit, ...modal } = props;

  const { payload, closeModal } = useModalInformation<Item.Base>(
    modal.modalKey
  );

  // TODO: Separate movies and series
  const hasTask = useIsAnyTaskRunningWithId([GetItemId(payload ?? {})]);

  const [tmdbid, setValue] = useState("");

  const [updating, setUpdating] = useState(false);

  const footer = (
    <AsyncButton
      noReset
      onChange={setUpdating}
      disabled={hasTask}
      promise={() => {
        if (payload) {
          const itemId = GetItemId(payload);
          return submit({
            id: [itemId],
            tmdbid: [tmdbid],
          });
        } else {
          return null;
        }
      }}
      onSuccess={() => {
        closeModal();
        onSuccess && payload && onSuccess(payload);
      }}
    >
      Fix Match and refresh
    </AsyncButton>
  );

  return (
    <BaseModal
      closeable={!updating}
      footer={footer}
      title={payload?.title}
      {...modal}
    >
      <Container fluid>
        <Form>
          {payload?.tmdbId ? (
            <Form.Group>
              <Form.Label>Actual TMDB ID</Form.Label>
              <Form.Control
                type="text"
                disabled
                defaultValue={payload?.tmdbId}
              ></Form.Control>
            </Form.Group>
          ) : null}
          <Form.Group>
            <Form.Label>Desired TMDB ID</Form.Label>
            <Form.Control
              type="text"
              required
              onChange={(e) => setValue(e.target.value)}
            ></Form.Control>
          </Form.Group>
        </Form>
      </Container>
    </BaseModal>
  );
};

export default FixMatch;
