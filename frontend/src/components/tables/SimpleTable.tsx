import { MutableRefObject, useEffect, useMemo, useRef } from "react";
import { useTable } from "@tanstack/react-table";
import BaseTable, { TableStyleProps } from "@/components/tables/BaseTable";
import {
  AppRow as Row,
  AppTable as Table,
  appTableFeatures,
  AppTableOptions as TableOptions,
  RowData,
} from "@/components/tables/features";
import { usePageSize } from "@/utilities/storage";

export type SimpleTableProps<T extends RowData> = Omit<
  TableOptions<T>,
  "features"
> & {
  instanceRef?: MutableRefObject<Table<T> | null>;
  tableStyles?: TableStyleProps<T>;
  onRowSelectionChanged?: (selectedRows: Row<T>[]) => void;
  onAllRowsExpandedChanged?: (isAllRowsExpanded: boolean) => void;
};

const SimpleTable = <T extends RowData>(props: SimpleTableProps<T>) => {
  const {
    instanceRef,
    tableStyles,
    onRowSelectionChanged,
    onAllRowsExpandedChanged,
    ...options
  } = props;

  const pageSize = usePageSize();

  const instance = useTable({
    features: appTableFeatures,
    ...options,
    autoResetPageIndex: false,
    autoResetExpanded: false,
    pageCount: pageSize,
    manualPagination: true,
  });

  useEffect(() => {
    if (instanceRef) {
      instanceRef.current = instance;
    }
  });

  const selectedRows = instance.getSelectedRowModel().rows;

  const memoizedRows = useMemo(() => selectedRows, [selectedRows]);

  const onRowSelectionChangedRef = useRef(onRowSelectionChanged);

  const isAllRowsExpanded = instance.getIsAllRowsExpanded();

  useEffect(() => {
    onRowSelectionChangedRef.current = onRowSelectionChanged;
  });

  useEffect(() => {
    onRowSelectionChangedRef.current?.(memoizedRows);
  }, [memoizedRows]);

  useEffect(() => {
    onAllRowsExpandedChanged?.(isAllRowsExpanded);
  }, [onAllRowsExpandedChanged, isAllRowsExpanded]);

  return <BaseTable tableStyles={tableStyles} instance={instance}></BaseTable>;
};

export default SimpleTable;
