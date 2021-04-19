import { isNull, isUndefined } from "lodash";
import React, { useCallback, useEffect } from "react";
import {
  PluginHook,
  TableOptions,
  usePagination,
  useRowSelect,
  useTable,
} from "react-table";
import { useReduxStore } from "../../@redux/hooks/base";
import { ScrollToTop } from "../../utilites";
import { AsyncStateOverlay } from "../async";
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

  const globalPageSize = useReduxStore((s) => s.site.pageSize);

  // Scroll to top when page is changed
  useEffect(() => {
    if (autoScroll) {
      ScrollToTop();
    }
  }, [pageIndex, autoScroll]);

  useEffect(() => {
    const selecting = options.isSelecting;
    if (canSelect && !isUndefined(selecting)) {
      if (selecting) {
        setPageSize(rows.length);
      } else {
        setPageSize(globalPageSize);
      }
    }
  }, [
    canSelect,
    globalPageSize,
    options.isSelecting,
    rows.length,
    setPageSize,
  ]);

  const total = options.asyncState
    ? options.asyncState.data.order.length
    : rows.length;

  const orderIdStateValidater = useCallback(
    (state: OrderIdState<any>) => {
      const start = pageIndex * pageSize;
      const end = start + pageSize;
      return state.order.slice(start, end).every(isNull) === false;
    },
    [pageIndex, pageSize]
  );

  if (needLoadingScreen && options.asyncState) {
    return (
      <AsyncStateOverlay
        state={options.asyncState}
        exist={orderIdStateValidater}
      ></AsyncStateOverlay>
    );
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
