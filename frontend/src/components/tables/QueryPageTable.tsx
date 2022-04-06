import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { ScrollToTop } from "@/utilities";
import { useEffect } from "react";
import { PluginHook, TableOptions, useTable } from "react-table";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import PageControl from "./PageControl";
import { useDefaultSettings } from "./plugins";

type Props<T extends object> = TableOptions<T> &
  TableStyleProps<T> & {
    plugins?: PluginHook<T>[];
    query: UsePaginationQueryResult<T>;
  };

export default function QueryPageTable<T extends object>(props: Props<T>) {
  const { plugins, query, ...remain } = props;
  const { style, options } = useStyleAndOptions(remain);

  const {
    data,
    isFetching,
    paginationStatus: { page, pageCount, totalCount, pageSize },
    controls: { gotoPage },
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

  return (
    <>
      <BaseTable
        {...style}
        placeholder={isFetching}
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
        goto={gotoPage}
        loading={isFetching}
      ></PageControl>
    </>
  );
}
