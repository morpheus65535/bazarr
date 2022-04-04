import { useIsAnyActionRunning, useLanguageProfiles } from "@/apis/hooks";
import {
  useModal,
  useModalControl,
  usePayload,
  withModal,
} from "@/modules/modals";
import { GetItemId } from "@/utilities";
import { Container } from "@mantine/core";
import { FunctionComponent, useMemo, useState } from "react";
import { UseMutationResult } from "react-query";
import { SelectorOption } from "..";
import { AsyncButton } from "../async";

interface Props {
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem, unknown>;
}

const Editor: FunctionComponent<Props> = ({ mutation }) => {
  const { data: profiles } = useLanguageProfiles();

  const payload = usePayload<Item.Base>();
  const { mutateAsync, isLoading } = mutation;

  const { hide } = useModalControl();

  const hasTask = useIsAnyActionRunning();

  const profileOptions = useMemo<SelectorOption<number>[]>(
    () =>
      profiles?.map((v) => {
        return { label: v.name, value: v.profileId };
      }) ?? [],
    [profiles]
  );

  const [id, setId] = useState<Nullable<number>>(payload?.profileId ?? null);

  const Modal = useModal({
    closeable: !isLoading,
    onMounted: () => {
      setId(payload?.profileId ?? null);
    },
  });

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
      onSuccess={() => hide()}
    >
      Save
    </AsyncButton>
  );

  return (
    <Modal title={payload?.title ?? "Item Editor"} footer={footer}>
      <Container fluid>
        {/* <Form>
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
        </Form> */}
      </Container>
    </Modal>
  );
};

export default withModal(Editor, "edit");
