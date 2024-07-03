import { MutableRefObject, useEffect, useMemo } from "react";
import {
  getCoreRowModel,
  Row,
  Table,
  TableOptions,
  useReactTable,
} from "@tanstack/react-table";
import NewBaseTable, {
  NewTableStyleProps,
} from "@/components/tables/NewBaseTable";
import { usePageSize } from "@/utilities/storage";

export type NewSimpleTableProps<T extends object> = Omit<
  TableOptions<T>,
  "getCoreRowModel"
> & {
  instanceRef?: MutableRefObject<Table<T> | null>;
  tableStyles?: NewTableStyleProps<T>;
  onRowSelectionChanged?: (selectedRows: Row<T>[]) => void;
};

export default function NewSimpleTable<T extends object>(
  props: NewSimpleTableProps<T>,
) {
  const { instanceRef, tableStyles, onRowSelectionChanged, ...options } = props;

  const pageSize = usePageSize();

  const instance = useReactTable({
    ...options,
    getCoreRowModel: getCoreRowModel(),
    autoResetPageIndex: false,
    autoResetExpanded: false,
    pageCount: pageSize,
  });

  if (instanceRef) {
    instanceRef.current = instance;
  }

  const selectedRows = instance.getSelectedRowModel().rows;
  const memoizedRows = useMemo(() => selectedRows, [selectedRows]);

  useEffect(() => {
    onRowSelectionChanged?.(memoizedRows);
  }, [onRowSelectionChanged, memoizedRows]);

  return (
    <NewBaseTable tableStyles={tableStyles} instance={instance}></NewBaseTable>
  );
}
