import { useIsAnyActionRunning, useLanguageProfiles } from "apis/hooks";
import React, { FunctionComponent, useEffect, useMemo, useState } from "react";
import { Container, Form } from "react-bootstrap";
import { UseMutationResult } from "react-query";
import { GetItemId } from "utilities";
import { AsyncButton, Selector } from "../";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useModalInformation } from "./hooks";

interface Props {
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem, unknown>;
}

const Editor: FunctionComponent<Props & BaseModalProps> = (props) => {
  const { mutation, ...modal } = props;

  const { data: profiles } = useLanguageProfiles();

  const { payload, closeModal } = useModalInformation<Item.Base>(
    modal.modalKey
  );

  const { mutateAsync, isLoading } = mutation;

  const hasTask = useIsAnyActionRunning();

  const profileOptions = useMemo<SelectorOption<number>[]>(
    () =>
      profiles?.map((v) => {
        return { label: v.name, value: v.profileId };
      }) ?? [],
    [profiles]
  );

  const [id, setId] = useState<Nullable<number>>(payload?.profileId ?? null);

  useEffect(() => {
    setId(payload?.profileId ?? null);
  }, [payload]);

  const footer = (
    <AsyncButton
      noReset
      disabled={hasTask}
      promise={() => {
        if (payload) {
          const itemId = GetItemId(payload);
          if (!itemId) {
            return null;
          }

          return mutateAsync({
            id: [itemId],
            profileid: [id],
          });
        } else {
          return null;
        }
      }}
      onSuccess={() => closeModal()}
    >
      Save
    </AsyncButton>
  );

  return (
    <BaseModal
      closeable={!isLoading}
      footer={footer}
      title={payload?.title}
      {...modal}
    >
      <Container fluid>
        <Form>
          <Form.Group>
            <Form.Label>Audio</Form.Label>
            <Form.Control
              type="text"
              disabled
              defaultValue={payload?.audio_language
                .map((v) => v.name)
                .join(", ")}
            ></Form.Control>
          </Form.Group>
          <Form.Group>
            <Form.Label>Languages Profiles</Form.Label>
            <Selector
              clearable
              disabled={hasTask}
              options={profileOptions}
              value={id}
              onChange={(v) => setId(v === undefined ? null : v)}
            ></Selector>
          </Form.Group>
        </Form>
      </Container>
    </BaseModal>
  );
};

export default Editor;
