import React, { FunctionComponent, useCallback } from "react";
import { TableUpdater } from "react-table";
import { ExtendItemComparer, SharedProps } from ".";
import { useLanguageProfiles } from "../../@redux/hooks";
import { ItemEditorModal, PageTable, useShowModal } from "../../components";
import { getExtendItemId, useMergeArray } from "../../utilites";

interface Props extends SharedProps {
  items: readonly Item.Base[];
  dirtyItems: readonly Item.Base[];
  editMode: boolean;
  select: React.Dispatch<Item.Base[]>;
}

const Table: FunctionComponent<Props> = ({
  items,
  dirtyItems,
  update,
  modify,
  editMode,
  select,
  columns,
  name,
}) => {
  const showModal = useShowModal();

  const updateRow = useCallback<TableUpdater<Item.Base>>(
    (row, modalKey: string) => {
      showModal(modalKey, row.original);
    },
    [showModal]
  );

  const data = useMergeArray(items, dirtyItems, ExtendItemComparer);

  const [profiles] = useLanguageProfiles();

  return (
    <React.Fragment>
      <PageTable
        columns={columns}
        data={data}
        loose={[profiles]}
        select={editMode}
        onSelect={select}
        emptyText={`No ${name} Found`}
        update={updateRow}
      ></PageTable>
      <ItemEditorModal
        modalKey="edit"
        submit={modify}
        onSuccess={(item) => {
          const id = getExtendItemId(item);
          update(id);
        }}
      ></ItemEditorModal>
    </React.Fragment>
  );
};

export default Table;
