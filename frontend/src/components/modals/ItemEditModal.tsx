import {
  useModal,
  useModalControl,
  usePayload,
  withModal,
} from "@/modules/modals";
import { FunctionComponent } from "react";
import { UseMutationResult } from "react-query";
import ItemEditForm from "../forms/ItemEditForm";

interface Props {
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem, unknown>;
}

const Editor: FunctionComponent<Props> = ({ mutation }) => {
  const payload = usePayload<Item.Base>();

  const { hide } = useModalControl();

  const Modal = useModal({
    closeable: mutation.isLoading,
  });

  return (
    <Modal title={payload?.title ?? "Item Editor"}>
      <ItemEditForm
        mutation={mutation}
        item={payload}
        onCancel={hide}
        onComplete={hide}
      ></ItemEditForm>
    </Modal>
  );
};

export default withModal(Editor, "edit");
