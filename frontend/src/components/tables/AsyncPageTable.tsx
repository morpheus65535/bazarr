import React, { useCallback, useEffect, useState } from "react";
import { useQuery } from "react-query";
import { PluginHook, TableOptions, useTable } from "react-table";
import { LoadingIndicator } from "..";
import { createRangeId, ScrollToTop } from "../../utilities";
import { usePageSize } from "../../utilities/storage";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import PageControl from "./PageControl";
import { useDefaultSettings } from "./plugins";

type Props<T extends object> = TableOptions<T> &
  TableStyleProps<T> & {
    plugins?: PluginHook<T>[];
    keys: string[];
    query: RangeQuery<T>;
  };

export default function AsyncPageTable<T extends object>(props: Props<T>) {
  const { plugins, query, keys, ...remain } = props;
  const { style, options } = useStyleAndOptions(remain);

  const [pageIndex, setIndex] = useState(0);
  const [pageSize] = usePageSize();

  const start = pageIndex * pageSize;

  const param: Parameter.Range = {
    start,
    length: pageSize,
  };

  const paramKey = createRangeId(keys[0], param);
  const { data, isLoading } = useQuery(
    [...keys, paramKey],
    () => query(param),
    {
      keepPreviousData: true,
    }
  );

  const total = data?.total ?? 0;
  const pageCount = Math.ceil(total / pageSize);

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

  const previous = useCallback(() => {
    setIndex((i) => Math.max(0, i - 1));
  }, []);

  const next = useCallback(() => {
    if (pageCount) {
      setIndex((i) => Math.min(i + 1, pageCount - 1));
    }
  }, [pageCount]);

  const goto = useCallback((idx: number) => {
    setIndex(idx);
  }, []);

  useEffect(() => {
    ScrollToTop();
  }, [pageIndex]);

  // Reset page index if we out of bound
  useEffect(() => {
    if (pageCount === undefined || pageCount === 0) return;

    if (pageIndex >= pageCount) {
      setIndex(pageCount - 1);
    } else if (pageIndex < 0) {
      setIndex(0);
    }
  }, [pageIndex, pageCount]);

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
        index={pageIndex}
        size={pageSize}
        total={total}
        canPrevious={pageIndex > 0}
        canNext={pageIndex < pageCount - 1}
        previous={previous}
        next={next}
        goto={goto}
      ></PageControl>
    </React.Fragment>
  );
}
