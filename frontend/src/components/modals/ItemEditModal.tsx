import { useModals, withModal } from "@/modules/modals";
import { FunctionComponent, useCallback } from "react";
import { UseMutationResult } from "react-query";
import ItemEditForm from "../forms/ItemEditForm";

interface Props {
  item: Item.Base;
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem, unknown>;
}

const Editor: FunctionComponent<Props> = ({ mutation, item }) => {
  const modals = useModals();

  const hide = useCallback(() => modals.closeSelf(), [modals]);

  return (
    <ItemEditForm
      mutation={mutation}
      item={item}
      onCancel={hide}
      onComplete={hide}
    ></ItemEditForm>
  );
};

export default withModal(Editor, "item-editor");
