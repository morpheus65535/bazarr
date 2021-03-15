import React from "react";
import { useSelector } from "react-redux";
import {
  PluginHook,
  TableOptions,
  usePagination,
  useRowSelect,
  useTable,
} from "react-table";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import PageControl from "./PageControl";
import { useAsyncPagination, useCustomSelection } from "./plugins";

type Props<T extends object> = TableOptions<T> &
  TableStyleProps & {
    async?: boolean;
    canSelect?: boolean;
  };

export default function PageTable<T extends object>(props: Props<T>) {
  const { async, canSelect, ...remain } = props;
  const { style, options } = useStyleAndOptions(remain);

  // Default Settings
  const site = useSelector<ReduxStore, ReduxStore.Site>((s) => s.site);

  if (options.autoResetPage === undefined) {
    options.autoResetPage = false;
  }

  if (options.initialState === undefined) {
    options.initialState = {};
  }

  if (options.initialState.pageSize === undefined) {
    options.initialState.pageSize = site.pageSize;
  }

  const plugins: PluginHook<T>[] = [usePagination];

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
    state: { pageIndex, pageSize },
  } = instance;

  const total = options.idState
    ? options.idState.data.order.length
    : rows.length;

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
