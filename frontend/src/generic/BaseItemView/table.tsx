import React, { FunctionComponent, useCallback, useMemo } from "react";
import { TableUpdater } from "react-table";
import { ExtendItemComparer, SharedProps } from ".";
import { useLanguageProfiles } from "../../@redux/hooks";
import { ItemEditorModal, PageTable, useShowModal } from "../../components";
import { buildOrderList, getExtendItemId, useMergeArray } from "../../utilites";

interface Props extends SharedProps {
  dirtyItems: readonly Item.Base[];
  editMode: boolean;
  select: React.Dispatch<Item.Base[]>;
}

const Table: FunctionComponent<Props> = ({
  state,
  dirtyItems,
  update,
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
        canSelect
        columns={columns}
        data={data}
        idState={state}
        idGetter={getExtendItemId}
        loader={loader}
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
