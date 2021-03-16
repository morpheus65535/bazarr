import React, { useEffect } from "react";
import {
  PluginHook,
  TableOptions,
  usePagination,
  useRowSelect,
  useTable,
} from "react-table";
import { LoadingIndicator } from "..";
import { ScrollToTop } from "../../utilites";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import PageControl from "./PageControl";
import {
  useAsyncPagination,
  useCustomSelection,
  useDefaultSettings,
} from "./plugins";

type Props<T extends object> = TableOptions<T> &
  TableStyleProps & {
    async?: boolean;
    canSelect?: boolean;
  };

export default function PageTable<T extends object>(props: Props<T>) {
  const { async, canSelect, ...remain } = props;
  const { style, options } = useStyleAndOptions(remain);

  const plugins: PluginHook<T>[] = [useDefaultSettings, usePagination];

  if (async) {
    plugins.push(useAsyncPagination);
  }

  if (canSelect) {
    plugins.push(useRowSelect, useCustomSelection);
  }

  const instance = useTable(options, ...plugins);

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
    state: { pageIndex, pageSize, pageToLoad, needLoadingScreen },
  } = instance;

  // Scroll to top when page is changed
  useEffect(ScrollToTop, [pageIndex]);

  const total = options.idState
    ? options.idState.data.order.length
    : rows.length;

  if (needLoadingScreen) {
    return <LoadingIndicator></LoadingIndicator>;
  }

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
        loadState={pageToLoad}
        count={pageCount}
        index={pageIndex}
        size={pageSize}
        total={total}
        canPrevious={canPreviousPage}
        canNext={canNextPage}
        previous={previousPage}
        next={nextPage}
        goto={gotoPage}
      ></PageControl>
    </React.Fragment>
  );
}
