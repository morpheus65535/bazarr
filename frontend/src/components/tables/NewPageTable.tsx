import { MutableRefObject, useEffect } from "react";
import {
  getCoreRowModel,
  getPaginationRowModel,
  Table,
  TableOptions,
  useReactTable,
} from "@tanstack/react-table";
import NewBaseTable from "@/components/tables/NewBaseTable";
import { ScrollToTop } from "@/utilities";
import { usePageSize } from "@/utilities/storage";
import PageControl from "./PageControl";

type Props<T extends object> = Omit<TableOptions<T>, "getCoreRowModel"> & {
  instanceRef?: MutableRefObject<Table<T> | null>;
  autoScroll?: boolean;
};

export default function NewPageTable<T extends object>(props: Props<T>) {
  const { instanceRef, autoScroll, ...options } = props;

  const instance = useReactTable({
    ...options,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    pageCount: usePageSize(),
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
      <NewBaseTable {...options} instance={instance}></NewBaseTable>
      <PageControl
        count={instance.getPageCount()}
        index={state.pagination.pageIndex}
        size={state.pagination.pageSize}
        total={instance.getRowCount()}
        goto={instance.setPageIndex}
      ></PageControl>
    </>
  );
}
