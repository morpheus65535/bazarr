import React, { FunctionComponent, useMemo, useState } from "react";
import { Container, Form } from "react-bootstrap";
import { AsyncButton, Selector } from "../";
import { useIsAnyTaskRunningWithId } from "../../@modules/task/hooks";
import { useLanguageProfiles } from "../../@redux/hooks";
import { GetItemId } from "../../utilities";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useModalInformation } from "./hooks";

interface Props {
  submit: (form: FormType.ModifyItem) => Promise<void>;
  onSuccess?: (item: Item.Base) => void;
}

const Editor: FunctionComponent<Props & BaseModalProps> = (props) => {
  const { onSuccess, submit, ...modal } = props;

  const profiles = useLanguageProfiles();

  const { payload, closeModal } = useModalInformation<Item.Base>(
    modal.modalKey
  );

  // TODO: Separate movies and series
  const hasTask = useIsAnyTaskRunningWithId([GetItemId(payload ?? {})]);

  const profileOptions = useMemo<SelectorOption<number>[]>(
    () =>
      profiles?.map((v) => {
        return { label: v.name, value: v.profileId };
      }) ?? [],
    [profiles]
  );
  const [id, setId] = useState<Nullable<number>>(null);

  const [monitored, setMonitored] = useState(false);

  const [updating, setUpdating] = useState(false);

  const footer = (
    <AsyncButton
      noReset
      onChange={setUpdating}
      disabled={hasTask}
      promise={() => {
        if (payload) {
          const itemId = GetItemId(payload);
          setId(id);
          setMonitored(monitored);
          return submit({
            id: [itemId],
            profileid: [id],
            monitored: [monitored ? "True" : "False"],
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
      Save
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
          <Form.Group>
            <Form.Label>Monitored</Form.Label>
            <Form.Check
              custom
              id={payload?.tmdbId.toString()}
              checked={monitored}
              onChange={(v) => setMonitored(v.target.checked)}
              label={"Download subtitles if available"}
            ></Form.Check>
          </Form.Group>
          {payload?.audio_language ? (
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
          ) : null}
          <Form.Group>
            <Form.Label>Languages Profiles</Form.Label>
            <Selector
              clearable
              disabled={hasTask}
              options={profileOptions}
              defaultValue={payload?.profileId}
              onChange={(v) => setId(v === undefined ? null : v)}
            ></Selector>
          </Form.Group>
        </Form>
      </Container>
    </BaseModal>
  );
};

export default Editor;
