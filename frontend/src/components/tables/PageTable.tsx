import React, { useEffect } from "react";
import {
  PluginHook,
  TableOptions,
  usePagination,
  useRowSelect,
  useTable,
} from "react-table";
import { ScrollToTop } from "../../utilites";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import PageControl from "./PageControl";
import { useCustomSelection, useDefaultSettings } from "./plugins";

type Props<T extends object> = TableOptions<T> &
  TableStyleProps<T> & {
    canSelect?: boolean;
    autoScroll?: boolean;
    plugins?: PluginHook<T>[];
  };

export default function PageTable<T extends object>(props: Props<T>) {
  const { autoScroll, canSelect, plugins, ...remain } = props;
  const { style, options } = useStyleAndOptions(remain);

  const allPlugins: PluginHook<T>[] = [useDefaultSettings, usePagination];

  if (canSelect) {
    allPlugins.push(useRowSelect, useCustomSelection);
  }

  if (plugins) {
    allPlugins.push(...plugins);
  }

  const instance = useTable(options, ...allPlugins);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,

    // page
    page,
    canNextPage,
    canPreviousPage,
    pageCount,
    gotoPage,
    nextPage,
    previousPage,
    state: { pageIndex, pageSize },
  } = instance;

  // Scroll to top when page is changed
  useEffect(() => {
    if (autoScroll) {
      ScrollToTop();
    }
  }, [pageIndex, autoScroll]);

  return (
    <React.Fragment>
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
        canPrevious={canPreviousPage}
        canNext={canNextPage}
        previous={previousPage}
        next={nextPage}
        goto={gotoPage}
      ></PageControl>
    </React.Fragment>
  );
}
