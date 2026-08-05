import { MutableRefObject, useEffect } from "react";
import { useTable } from "@tanstack/react-table";
import BaseTable, { TableStyleProps } from "@/components/tables/BaseTable";
import {
  AppTable as Table,
  appTableFeatures,
  AppTableOptions as TableOptions,
  RowData,
} from "@/components/tables/features";
import { ScrollToTop } from "@/utilities";
import { usePageSize } from "@/utilities/storage";
import PageControl from "./PageControl";

type Props<T extends RowData> = Omit<TableOptions<T>, "features"> & {
  instanceRef?: MutableRefObject<Table<T> | null>;
  tableStyles?: TableStyleProps<T>;
  autoScroll?: boolean;
};

const PageTable = <T extends RowData>(props: Props<T>) => {
  const { instanceRef, autoScroll, ...options } = props;

  const pageSize = usePageSize();

  const instance = useTable({
    features: appTableFeatures,
    ...options,
    initialState: {
      pagination: {
        pageIndex: 0,
        pageSize: pageSize,
      },
    },
  });

  if (instanceRef) {
    instanceRef.current = instance;
  }

  const state = instance.state;
  const pageIndex = state.pagination.pageIndex;

  // Scroll to top when page is changed
  useEffect(() => {
    if (autoScroll) {
      ScrollToTop();
    }
  }, [pageIndex, autoScroll]);

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
};

export default PageTable;
