import { MutableRefObject, useEffect, useMemo } from "react";
import {
  getCoreRowModel,
  Row,
  Table,
  TableOptions,
  useReactTable,
} from "@tanstack/react-table";
import BaseTable, { TableStyleProps } from "@/components/tables/BaseTable";
import { usePageSize } from "@/utilities/storage";

export type SimpleTableProps<T extends object> = Omit<
  TableOptions<T>,
  "getCoreRowModel"
> & {
  instanceRef?: MutableRefObject<Table<T> | null>;
  tableStyles?: TableStyleProps<T>;
  onRowSelectionChanged?: (selectedRows: Row<T>[]) => void;
  onAllRowsExpandedChanged?: (isAllRowsExpanded: boolean) => void;
};

export default function SimpleTable<T extends object>(
  props: SimpleTableProps<T>,
) {
  const {
    instanceRef,
    tableStyles,
    onRowSelectionChanged,
    onAllRowsExpandedChanged,
    ...options
  } = props;

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

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const memoizedRowSelectionChanged = useMemo(() => onRowSelectionChanged, []);

  const isAllRowsExpanded = instance.getIsAllRowsExpanded();

  useEffect(() => {
    memoizedRowSelectionChanged?.(memoizedRows);
  }, [memoizedRowSelectionChanged, memoizedRows]);

  useEffect(() => {
    onAllRowsExpandedChanged?.(isAllRowsExpanded);
  }, [onAllRowsExpandedChanged, isAllRowsExpanded]);

  return <BaseTable tableStyles={tableStyles} instance={instance}></BaseTable>;
}
