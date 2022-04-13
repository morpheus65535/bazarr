import { ScrollToTop } from "@/utilities";
import { useEffect } from "react";
import { PluginHook, TableOptions, usePagination, useTable } from "react-table";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import PageControl from "./PageControl";
import { useDefaultSettings } from "./plugins";

type Props<T extends object> = TableOptions<T> &
  TableStyleProps<T> & {
    autoScroll?: boolean;
    plugins?: PluginHook<T>[];
  };

const tablePlugins = [useDefaultSettings, usePagination];

export default function PageTable<T extends object>(props: Props<T>) {
  const { autoScroll, plugins, ...remain } = props;
  const { style, options } = useStyleAndOptions(remain);

  const instance = useTable(options, ...tablePlugins, ...(plugins ?? []));

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,

    // page
    page,
    pageCount,
    gotoPage,
    state: { pageIndex, pageSize },
  } = instance;

  // Scroll to top when page is changed
  useEffect(() => {
    if (autoScroll) {
      ScrollToTop();
    }
  }, [pageIndex, autoScroll]);

  return (
    <>
      <BaseTable
        {...style}
        headers={headerGroups}
        rows={page}
        prepareRow={prepareRow}
        tableProps={getTableProps()}
        tableBodyProps={getTableBodyProps()}
      ></BaseTable>
      <PageControl
        count={pageCount}
        index={pageIndex}
        size={pageSize}
        total={rows.length}
        goto={gotoPage}
      ></PageControl>
    </>
  );
}
