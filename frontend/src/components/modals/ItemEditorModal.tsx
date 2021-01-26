import React, { FunctionComponent, useMemo, useState } from "react";
import { connect } from "react-redux";
import { Container, Form } from "react-bootstrap";

import BasicModal, { BasicModalProps } from "./BasicModal";

import { Selector, AsyncButton } from "../";
import { useCloseModal, usePayload } from "./provider";

interface Props {
  profiles: LanguagesProfile[];
  submit: (item: ExtendItem, form: ItemModifyForm) => Promise<void>;
  onSuccess?: (item: ExtendItem) => void;
}

function mapStateToProps({ system }: StoreState) {
  return {
    profiles: system.languagesProfiles.items,
  };
}

const Editor: FunctionComponent<Props & BasicModalProps> = (props) => {
  const { profiles, onSuccess, submit, ...modal } = props;

  const item = usePayload<ExtendItem>();

  const closeModal = useCloseModal();

  const profileOptions = useMemo<Pair[]>(
    () =>
      profiles.map<Pair>((v) => {
        return { key: v.profileId.toString(), value: v.name };
      }),
    [profiles]
  );
  const [id, setId] = useState<number | undefined>(undefined);

  const [updating, setUpdating] = useState(false);

  const footer = useMemo(
    () => (
      <AsyncButton
        disabled={id === undefined}
        onChange={setUpdating}
        promise={() =>
          submit(item!, {
            profileid: id,
          })
        }
        success={() => {
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
    <BasicModal
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
              nullKey="None"
              options={profileOptions}
              defaultKey={item?.profileId?.toString()}
              onSelect={(k) => {
                const id = parseInt(k);

                if (!isNaN(id)) {
                  setId(id);
                } else {
                  setId(undefined);
                }
              }}
            ></Selector>
          </Form.Group>
        </Form>
      </Container>
    </BasicModal>
  );
};

export default connect(mapStateToProps)(Editor);
