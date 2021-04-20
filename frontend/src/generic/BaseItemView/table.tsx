import { uniqBy } from "lodash";
import React, { useCallback, useMemo } from "react";
import { TableUpdater } from "react-table";
import { SharedProps } from ".";
import { useLanguageProfiles } from "../../@redux/hooks";
import { ItemEditorModal, PageTable, useShowModal } from "../../components";
import { buildOrderList, GetItemId } from "../../utilites";

interface Props<T extends Item.Base> extends SharedProps<T> {
  dirtyItems: readonly T[];
  editMode: boolean;
  select: React.Dispatch<T[]>;
}

function Table<T extends Item.Base>({
  state,
  dirtyItems,
  modify,
  editMode,
  select,
  columns,
  loader,
  name,
}: Props<T>) {
  const showModal = useShowModal();

  const updateRow = useCallback<TableUpdater<T>>(
    (row, modalKey: string) => {
      showModal(modalKey, row.original);
    },
    [showModal]
  );

  const idState = state.data;

  const orderList = useMemo(() => buildOrderList(idState), [idState]);

  const data = useMemo(() => uniqBy([...dirtyItems, ...orderList], GetItemId), [
    dirtyItems,
    orderList,
  ]);

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
}

export default Table;
