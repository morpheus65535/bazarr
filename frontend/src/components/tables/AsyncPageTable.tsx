import React, { useCallback, useEffect, useState } from "react";
import { PluginHook, TableOptions, useTable } from "react-table";
import { LoadingIndicator } from "..";
import { usePageSize } from "../../@storage/local";
import {
  ScrollToTop,
  useEntityByRange,
  useIsEntityLoaded,
} from "../../utilities";
import BaseTable, { TableStyleProps, useStyleAndOptions } from "./BaseTable";
import PageControl from "./PageControl";
import { useDefaultSettings } from "./plugins";

function useEntityPagination<T>(
  entity: Async.Entity<T>,
  loader: (range: Parameter.Range) => void,
  start: number,
  end: number
): T[] {
  const { state, content } = entity;

  const needInit = state === "uninitialized";
  const hasEmpty = useIsEntityLoaded(content, start, end) === false;

  useEffect(() => {
    if (needInit || hasEmpty) {
      const length = end - start;
      loader({ start, length });
    }
  });

  return useEntityByRange(content, start, end);
}

type Props<T extends object> = TableOptions<T> &
  TableStyleProps<T> & {
    plugins?: PluginHook<T>[];
    entity: Async.Entity<T>;
    loader: (params: Parameter.Range) => void;
  };

export default function AsyncPageTable<T extends object>(props: Props<T>) {
  const { entity, plugins, loader, ...remain } = props;
  const { style, options } = useStyleAndOptions(remain);

  const {
    state,
    content: { ids },
  } = entity;

  // Impl a new pagination system instead of hacking into existing one
  const [pageIndex, setIndex] = useState(0);
  const [pageSize] = usePageSize();
  const totalRows = ids.length;
  const pageCount = Math.ceil(totalRows / pageSize);

  const pageStart = pageIndex * pageSize;
  const pageEnd = pageStart + pageSize;

  const data = useEntityPagination(entity, loader, pageStart, pageEnd);

  const instance = useTable(
    {
      ...options,
      data,
    },
    useDefaultSettings,
    ...(plugins ?? [])
  );

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } =
    instance;

  const previous = useCallback(() => {
    setIndex((idx) => idx - 1);
  }, []);

  const next = useCallback(() => {
    setIndex((idx) => idx + 1);
  }, []);

  const goto = useCallback((idx: number) => {
    setIndex(idx);
  }, []);

  useEffect(() => {
    ScrollToTop();
  }, [pageIndex]);

  // Reset page index if we out of bound
  useEffect(() => {
    if (pageCount === 0) return;

    if (pageIndex >= pageCount) {
      setIndex(pageCount - 1);
    } else if (pageIndex < 0) {
      setIndex(0);
    }
  }, [pageIndex, pageCount]);

  if ((state === "loading" && data.length === 0) || state === "uninitialized") {
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
