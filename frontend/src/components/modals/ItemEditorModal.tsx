import React, { FunctionComponent, useMemo, useState } from "react";
import { Container, Form } from "react-bootstrap";
import { AsyncButton, Selector } from "../";
import { useLanguageProfiles } from "../../@redux/hooks";
import { GetItemId } from "../../utilites";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useCloseModal, usePayload } from "./provider";

interface Props {
  submit: (form: FormType.ModifyItem) => Promise<void>;
  onSuccess?: (item: Item.Base) => void;
}

const Editor: FunctionComponent<Props & BaseModalProps> = (props) => {
  const { onSuccess, submit, ...modal } = props;

  const [profiles] = useLanguageProfiles();

  const item = usePayload<Item.Base>(modal.modalKey);

  const closeModal = useCloseModal();

  const profileOptions = useMemo<SelectorOption<number>[]>(
    () =>
      profiles.map((v) => {
        return { label: v.name, value: v.profileId };
      }),
    [profiles]
  );
  const [id, setId] = useState<Nullable<number>>(null);

  const [updating, setUpdating] = useState(false);

  const footer = useMemo(
    () => (
      <AsyncButton
        onChange={setUpdating}
        promise={() => {
          if (item) {
            const itemId = GetItemId(item);
            return submit({
              id: [itemId],
              profileid: [id],
            });
          } else {
            return null;
          }
        }}
        onSuccess={() => {
          closeModal();
          onSuccess && item && onSuccess(item);
        }}
      >
        Save
      </AsyncButton>
    ),
    [closeModal, id, item, onSuccess, submit]
  );

  return (
    <BaseModal
      closeable={!updating}
      footer={footer}
      title={item?.title}
      {...modal}
    >
      <Container fluid>
        <Form>
          <Form.Group>
            <Form.Label>Audio</Form.Label>
            <Form.Control
              type="text"
              disabled
              defaultValue={item?.audio_language.map((v) => v.name).join(", ")}
            ></Form.Control>
          </Form.Group>
          <Form.Group>
            <Form.Label>Languages Profiles</Form.Label>
            <Selector
              clearable
              options={profileOptions}
              defaultValue={item?.profileId}
              onChange={(v) => setId(v === undefined ? null : v)}
            ></Selector>
          </Form.Group>
        </Form>
      </Container>
    </BaseModal>
  );
};

export default Editor;
