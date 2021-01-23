import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { connect } from "react-redux";
import { Container, Form } from "react-bootstrap";

import BasicModal, { BasicModalProps } from "./BasicModal";

import { Selector, AsyncButton } from "../";

interface Props {
  profiles: LanguagesProfile[];
  item?: ExtendItem;
  submit: (form: ItemModifyForm) => Promise<void>;
  onSuccess?: () => void;
}

function mapStateToProps({ system }: StoreState) {
  return {
    profiles: system.languagesProfiles.items,
  };
}

const Editor: FunctionComponent<Props & BasicModalProps> = (props) => {
  const { item, profiles, onSuccess, submit, ...modal } = props;

  const submitForm = useCallback(
    (form: ItemModifyForm) => {
      return submit(form);
    },
    [submit]
  );

  const profileOptions = useMemo<Pair[]>(
    () =>
      profiles.map<Pair>((v) => {
        return { key: v.profileId.toString(), value: v.name };
      }),
    [profiles]
  );
  const [id, setId] = useState(item?.profileId);
  const [updating, setUpdating] = useState(false);

  const footer = (
    <AsyncButton
      onChange={setUpdating}
      promise={() =>
        submitForm({
          profileid: id,
        })
      }
      success={onSuccess}
    >
      Save
    </AsyncButton>
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
              defaultKey={id?.toString()}
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
