import { UsePaginationQueryResult } from "@/apis/queries/hooks";
import { ScrollToTop } from "@/utilities";
import { Box, Skeleton } from "@mantine/core";
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
    return (
      <Box mx={10}>
        <div>
          {Array(pageSize)
            .fill(0)
            .map((_, i) => (
              <Skeleton key={i} radius="xl" height={24} mt={10}></Skeleton>
            ))}
        </div>
      </Box>
    );
  }

  return (
    <>
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
    </>
  );
}
