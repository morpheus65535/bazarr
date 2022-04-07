import { useModals, withModal } from "@/modules/modals";
import { FunctionComponent } from "react";
import { UseMutationResult } from "react-query";
import ItemEditForm from "../forms/ItemEditForm";

interface Props {
  item: Item.Base;
  mutation: UseMutationResult<void, unknown, FormType.ModifyItem, unknown>;
}

const Editor: FunctionComponent<Props> = ({ mutation, item }) => {
  const modals = useModals();

  return (
    <ItemEditForm
      mutation={mutation}
      item={item}
      onCancel={modals.closeSelf}
      onComplete={modals.closeSelf}
    ></ItemEditForm>
  );
};

export default withModal(Editor, "item-editor", {
  title: "Editor",
  size: "md",
});
