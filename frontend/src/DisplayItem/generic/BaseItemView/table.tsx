import React, { useCallback } from "react";
import { TableOptions, TableUpdater } from "react-table";
import { SharedProps } from ".";
import {
  AsyncPageTable,
  ItemEditorModal,
  useShowModal,
} from "../../../components";
import { TableStyleProps } from "../../../components/tables/BaseTable";

interface Props<T extends Item.Base> extends SharedProps<T> {
  dirtyItems: readonly T[];
  editMode: boolean;
  select: React.Dispatch<T[]>;
}

function Table<T extends Item.Base>({
  dirtyItems,
  modify,
  editMode,
  select,
  columns,
  name,
  query,
  keys,
}: Props<T>) {
  const showModal = useShowModal();

  const updateRow = useCallback<TableUpdater<T>>(
    (row, modalKey: string) => {
      showModal(modalKey, row.original);
    },
    [showModal]
  );

  // const data = useMemo(
  //   () => uniqBy([...dirtyItems, ...orderList], GetItemId),
  //   [dirtyItems, orderList]
  // );

  const options: Partial<TableOptions<T> & TableStyleProps<T>> = {
    emptyText: `No ${name} Found`,
    update: updateRow,
  };

  return (
    <React.Fragment>
      <AsyncPageTable
        {...options}
        columns={columns}
        keys={keys}
        query={query}
        data={[]}
      ></AsyncPageTable>
      <ItemEditorModal modalKey="edit" submit={modify}></ItemEditorModal>
    </React.Fragment>
  );
}

export default Table;
