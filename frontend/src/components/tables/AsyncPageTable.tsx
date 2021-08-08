import React, { useCallback, useEffect, useMemo, useState } from "react";
import { PluginHook, TableOptions, useTable } from "react-table";
import { LoadingIndicator } from "..";
import { usePageSize } from "../../@storage/local";
import {
  ScrollToTop,
  useAsyncHasDirtyInRange,
  useEntityContentByRange,
} from "../../utilites";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import PageControl from "./PageControl";
import { useDefaultSettings } from "./plugins";

type Props<T extends object> = TableOptions<T> &
  TableStyleProps<T> & {
    plugins?: PluginHook<T>[];
    entity: Async.Entity<T>;
    loader: (params: Parameter.Range) => void;
  };

export default function AsyncPageTable<T extends object>(props: Props<T>) {
  const { entity, plugins, loader, ...remain } = props;
  const { style, options } = useStyleAndOptions(remain);

  const { state, content } = entity;

  const ids = content.ids;

  const allPlugins: PluginHook<T>[] = [useDefaultSettings];

  if (plugins) {
    allPlugins.push(...plugins);
  }

  // Impl a new pagination system instead of hooking into the existing one
  const [pageIndex, setIndex] = useState(0);
  const [pageSize] = usePageSize();
  const totalRows = ids.length;
  const pageCount = Math.ceil(totalRows / pageSize);

  const previous = useCallback(() => {
    setIndex((idx) => idx - 1);
  }, []);

  const next = useCallback(() => {
    setIndex((idx) => idx + 1);
  }, []);

  const goto = useCallback((idx: number) => {
    setIndex(idx);
  }, []);

  const pageStart = pageIndex * pageSize;
  const pageEnd = pageStart + pageSize;

  const data = useEntityContentByRange(content, pageStart, pageEnd);

  const newOptions = useMemo<TableOptions<T>>(
    () => ({
      ...options,
      data,
    }),
    [options, data]
  );

  const instance = useTable(newOptions, ...allPlugins);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = instance;

  useEffect(() => {
    ScrollToTop();
  }, [pageIndex]);

  const needFetch = data.length === 0 && state !== "loading";
  const needRefresh = useAsyncHasDirtyInRange(entity, pageStart, pageEnd);

  useEffect(() => {
    if (needFetch || needRefresh) {
      loader({ start: pageStart, length: pageSize });
    }
  }, [pageStart, pageSize, loader, needFetch, needRefresh]);

  if (state === "loading" && data.length === 0) {
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
        total={totalRows}
        canPrevious={pageIndex > 0}
        canNext={pageIndex < pageCount - 1}
        previous={previous}
        next={next}
        goto={goto}
      ></PageControl>
    </React.Fragment>
  );
}
