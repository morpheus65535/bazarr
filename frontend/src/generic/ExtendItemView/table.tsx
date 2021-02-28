import React, { FunctionComponent, useCallback, useMemo } from "react";
import { TableOptions, TableUpdater } from "react-table";
import { SharedProps } from ".";
import {
  ItemEditorModal,
  PageTable,
  SelectTable,
  useShowModal,
} from "../../components";
import { getExtendItemId, useMergeArray } from "../../utilites";

interface Props extends SharedProps {
  items: readonly ExtendItem[];
  dirtyItems: readonly ExtendItem[];
  editMode: boolean;
  select: React.Dispatch<ExtendItem[]>;
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
  profiles,
}) => {
  const showModal = useShowModal();

  const updateRow = useCallback<TableUpdater<ExtendItem>>(
    (row, modalKey: string) => {
      showModal(modalKey, row.original);
    },
    [showModal]
  );

  const data = useMergeArray(items, dirtyItems, "title");

  const sharedOptions: TableOptions<ExtendItem> = useMemo(
    () => ({ columns, data, loose: [profiles] }),
    [columns, data, profiles]
  );

  return (
    <React.Fragment>
      {editMode ? (
        <SelectTable {...sharedOptions} onSelect={select}></SelectTable>
      ) : (
        <PageTable
          {...sharedOptions}
          emptyText={`No ${name} Found`}
          update={updateRow}
        ></PageTable>
      )}
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
