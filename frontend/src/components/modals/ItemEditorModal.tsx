import React, { FunctionComponent, useMemo, useState } from "react";
import { Container, Form } from "react-bootstrap";
import { connect } from "react-redux";
import { AsyncButton, Selector } from "../";
import { getExtendItemId } from "../../utilites";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useCloseModal, usePayload } from "./provider";

interface Props {
  profiles: LanguagesProfile[];
  submit: (form: ItemModifyForm) => Promise<void>;
  onSuccess?: (item: ExtendItem) => void;
}

function mapStateToProps({ system }: StoreState) {
  return {
    profiles: system.languagesProfiles.items,
  };
}

const Editor: FunctionComponent<Props & BaseModalProps> = (props) => {
  const { profiles, onSuccess, submit, ...modal } = props;

  const item = usePayload<ExtendItem>(modal.modalKey);

  const closeModal = useCloseModal();

  const profileOptions = useMemo<SelectorOption<number>[]>(
    () =>
      profiles.map((v) => {
        return { label: v.name, value: v.profileId };
      }),
    [profiles]
  );
  const [id, setId] = useState<number | undefined>(undefined);

  const [updating, setUpdating] = useState(false);

  const footer = useMemo(
    () => (
      <AsyncButton
        onChange={setUpdating}
        promise={() => {
          const itemId = getExtendItemId(item!);
          return submit({
            id: [itemId],
            profileid: [id],
          });
        }}
        onSuccess={() => {
          closeModal();
          onSuccess && onSuccess(item!);
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
              onChange={setId}
            ></Selector>
          </Form.Group>
        </Form>
      </Container>
    </BaseModal>
  );
};

export default connect(mapStateToProps)(Editor);
