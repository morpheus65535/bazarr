import { isUndefined } from "lodash";
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
  TableStyleProps<T> & {
    async?: boolean;
    canSelect?: boolean;
    autoScroll?: boolean;
    plugins?: PluginHook<T>[];
  };

export default function PageTable<T extends object>(props: Props<T>) {
  const { async, autoScroll, canSelect, plugins, ...remain } = props;
  const { style, options } = useStyleAndOptions(remain);

  const allPlugins: PluginHook<T>[] = [useDefaultSettings, usePagination];

  if (async) {
    allPlugins.push(useAsyncPagination);
  }

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

    initialState,

    // page
    page,
    canNextPage,
    canPreviousPage,
    pageCount,
    gotoPage,
    nextPage,
    previousPage,
    setPageSize,
    state: { pageIndex, pageSize, pageToLoad, needLoadingScreen },
  } = instance;

  // Scroll to top when page is changed
  useEffect(() => {
    if (autoScroll) {
      ScrollToTop();
    }
  }, [pageIndex, autoScroll]);

  useEffect(() => {
    const selecting = options.isSelecting;
    const defaultSize = initialState?.pageSize;
    if (canSelect && !isUndefined(selecting) && !isUndefined(defaultSize)) {
      if (selecting) {
        setPageSize(rows.length);
      } else {
        setPageSize(defaultSize);
      }
    }
  }, [
    canSelect,
    initialState?.pageSize,
    options.isSelecting,
    rows.length,
    setPageSize,
  ]);

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
