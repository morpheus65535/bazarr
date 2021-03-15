import React from "react";
import { useSelector } from "react-redux";
import {
  TableOptions,
  usePagination,
  useRowSelect,
  useTable,
} from "react-table";
import BaseTable, {
  ExtractStyleAndOptions,
  TableStyleProps,
} from "./BaseTable";
import PageControl from "./PageControl";
import { useCustomSelection } from "./plugins";

type Props<T extends object> = TableOptions<T> & TableStyleProps & {};

export default function PageTable<T extends object>(props: Props<T>) {
  const { ...remain } = props;
  const { style, options } = ExtractStyleAndOptions(remain);

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

  const instance = useTable(
    options,
    usePagination,
    useRowSelect,
    useCustomSelection
  );

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
