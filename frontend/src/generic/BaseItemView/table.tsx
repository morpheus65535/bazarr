import React, { FunctionComponent, useCallback, useMemo } from "react";
import { TableOptions, TableUpdater } from "react-table";
import { ExtendItemComparer, SharedProps } from ".";
import {
  ItemEditorModal,
  PageTable,
  SelectTable,
  useShowModal,
} from "../../components";
import {
  getExtendItemId,
  useLanguageProfiles,
  useMergeArray,
} from "../../utilites";

interface Props extends SharedProps {
  items: readonly BaseItem[];
  dirtyItems: readonly BaseItem[];
  editMode: boolean;
  select: React.Dispatch<BaseItem[]>;
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

  const updateRow = useCallback<TableUpdater<BaseItem>>(
    (row, modalKey: string) => {
      showModal(modalKey, row.original);
    },
    [showModal]
  );

  const data = useMergeArray(items, dirtyItems, ExtendItemComparer);

  const profiles = useLanguageProfiles();

  const sharedOptions: TableOptions<BaseItem> = useMemo(
    () => ({
      columns,
      data,
      loose: [profiles],
    }),
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
