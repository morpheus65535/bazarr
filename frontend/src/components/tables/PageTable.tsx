import { MutableRefObject, useEffect } from "react";
import {
  getCoreRowModel,
  getPaginationRowModel,
  Table,
  TableOptions,
  useReactTable,
} from "@tanstack/react-table";
import BaseTable, { TableStyleProps } from "@/components/tables/BaseTable";
import { ScrollToTop } from "@/utilities";
import { usePageSize } from "@/utilities/storage";
import PageControl from "./PageControl";

type Props<T extends object> = Omit<TableOptions<T>, "getCoreRowModel"> & {
  instanceRef?: MutableRefObject<Table<T> | null>;
  tableStyles?: TableStyleProps<T>;
  autoScroll?: boolean;
};

export default function PageTable<T extends object>(props: Props<T>) {
  const { instanceRef, autoScroll, ...options } = props;

  const pageSize = usePageSize();

  const instance = useReactTable({
    ...options,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: pageSize,
      },
    },
  });

  if (instanceRef) {
    instanceRef.current = instance;
  }

  const pageIndex = instance.getState().pagination.pageIndex;

  // Scroll to top when page is changed
  useEffect(() => {
    if (autoScroll) {
      ScrollToTop();
    }
  }, [pageIndex, autoScroll]);

  const state = instance.getState();

  return (
    <>
      <BaseTable {...options} instance={instance}></BaseTable>
      <PageControl
        count={instance.getPageCount()}
        index={state.pagination.pageIndex}
        size={pageSize}
        total={instance.getRowCount()}
        goto={instance.setPageIndex}
      ></PageControl>
    </>
  );
}
