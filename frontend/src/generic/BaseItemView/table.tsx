import React, { FunctionComponent, useCallback, useMemo } from "react";
import { TableUpdater } from "react-table";
import { ExtendItemComparer, SharedProps } from ".";
import { useLanguageProfiles } from "../../@redux/hooks";
import { ItemEditorModal, PageTable, useShowModal } from "../../components";
import { buildOrderList, GetItemId, useMergeArray } from "../../utilites";

interface Props extends SharedProps {
  dirtyItems: readonly Item.Base[];
  editMode: boolean;
  select: React.Dispatch<Item.Base[]>;
}

const Table: FunctionComponent<Props> = ({
  state,
  dirtyItems,
  modify,
  editMode,
  select,
  columns,
  loader,
  name,
}) => {
  const showModal = useShowModal();

  const updateRow = useCallback<TableUpdater<Item.Base>>(
    (row, modalKey: string) => {
      showModal(modalKey, row.original);
    },
    [showModal]
  );

  const idState = state.data;

  const orderList = useMemo(() => buildOrderList(idState), [idState]);

  const data = useMergeArray(orderList, dirtyItems, ExtendItemComparer);

  const [profiles] = useLanguageProfiles();

  return (
    <React.Fragment>
      <PageTable
        async
        autoScroll
        canSelect
        columns={columns}
        data={data}
        asyncState={state}
        asyncId={GetItemId}
        asyncLoader={loader}
        loose={[profiles]}
        isSelecting={editMode}
        onSelect={select}
        emptyText={`No ${name} Found`}
        externalUpdate={updateRow}
      ></PageTable>
      <ItemEditorModal modalKey="edit" submit={modify}></ItemEditorModal>
    </React.Fragment>
  );
};

export default Table;
