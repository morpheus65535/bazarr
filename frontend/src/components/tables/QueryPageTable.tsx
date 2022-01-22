import React, { useEffect } from "react";
import { PluginHook, TableOptions, useTable } from "react-table";
import { PaginationQuery } from "src/apis/queries/hooks";
import { LoadingIndicator } from "..";
import { ScrollToTop } from "../../utilities";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import PageControl from "./PageControl";
import { useDefaultSettings } from "./plugins";

type Props<T extends object> = TableOptions<T> &
  TableStyleProps<T> & {
    plugins?: PluginHook<T>[];
    query: PaginationQuery<T>;
  };

export default function QueryPageTable<T extends object>(props: Props<T>) {
  const { plugins, query, ...remain } = props;
  const { style, options } = useStyleAndOptions(remain);

  const {
    data,
    isLoading,
    paginationStatus: {
      page,
      pageCount,
      totalCount,
      canPrevious,
      canNext,
      pageSize,
    },
    controls: { previousPage, nextPage, gotoPage },
  } = query;

  const instance = useTable(
    {
      ...options,
      data: data?.data ?? [],
    },
    useDefaultSettings,
    ...(plugins ?? [])
  );

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } =
    instance;

  useEffect(() => {
    ScrollToTop();
  }, [page]);

  if (isLoading) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  return (
    <React.Fragment>
      <BaseTable
        {...style}
        headers={headerGroups}
        rows={rows}
        prepareRow={prepareRow}
        tableProps={getTableProps()}
        tableBodyProps={getTableBodyProps()}
      ></BaseTable>
      <PageControl
        count={pageCount}
        index={page}
        size={pageSize}
        total={totalCount}
        canPrevious={canPrevious}
        canNext={canNext}
        previous={previousPage}
        next={nextPage}
        goto={gotoPage}
      ></PageControl>
    </React.Fragment>
  );
}
