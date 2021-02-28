import React, { useMemo } from "react";
import { Table } from "react-bootstrap";
import {
  HeaderGroup,
  Row,
  TableBodyProps,
  TableOptions,
  TableProps,
} from "react-table";

export interface BaseTableProps<T extends object> extends TableStyleProps {
  // Table Options
  headers: HeaderGroup<T>[];
  rows: Row<T>[];
  headersRenderer?: (headers: HeaderGroup<T>[]) => JSX.Element[];
  rowRenderer?: (row: Row<T>) => JSX.Element | null;
  prepareRow: (row: Row<T>) => void;
  tableProps: TableProps;
  tableBodyProps: TableBodyProps;
}

export interface TableStyleProps {
  emptyText?: string;
  responsive?: boolean;
  hoverable?: boolean;
  striped?: boolean;
  borderless?: boolean;
  small?: boolean;
  hideHeader?: boolean;
}

interface ExtractResult<T extends object> {
  style: TableStyleProps;
  options: TableOptions<T>;
}

export function ExtractStyleAndOptions<T extends object>(
  props: TableStyleProps & TableOptions<T>
): ExtractResult<T> {
  const {
    emptyText,
    responsive,
    hoverable,
    striped,
    borderless,
    small,
    hideHeader,
    ...options
  } = props;
  return {
    style: {
      emptyText,
      responsive,
      hoverable,
      striped,
      borderless,
      small,
      hideHeader,
    },
    options,
  };
}

function DefaultHeaderRenderer<T extends object>(
  headers: HeaderGroup<T>[]
): JSX.Element[] {
  return headers.map((col) => (
    <th {...col.getHeaderProps()}>{col.render("Header")}</th>
  ));
}

function DefaultRowRenderer<T extends object>(row: Row<T>): JSX.Element | null {
  return (
    <tr {...row.getRowProps()}>
      {row.cells.map((cell) => (
        <td className={cell.column.className} {...cell.getCellProps()}>
          {cell.render("Cell")}
        </td>
      ))}
    </tr>
  );
}

export default function BaseTable<T extends object>(props: BaseTableProps<T>) {
  const {
    emptyText,
    responsive,
    hoverable,
    striped,
    borderless,
    small,
    hideHeader,

    headers,
    rows,
    headersRenderer,
    rowRenderer,
    prepareRow,
    tableProps,
    tableBodyProps,
  } = props;

  const colCount = useMemo(() => {
    return headers.reduce(
      (prev, curr) => (curr.headers.length > prev ? curr.headers.length : prev),
      0
    );
  }, [headers]);

  const empty = rows.length === 0;

  const hRenderer = headersRenderer ?? DefaultHeaderRenderer;
  const rRenderer = rowRenderer ?? DefaultRowRenderer;

  return (
    <Table
      size={small ? "sm" : undefined}
      striped={striped ?? true}
      borderless={borderless ?? true}
      hover={hoverable}
      responsive={responsive ?? true}
      {...tableProps}
    >
      <thead hidden={hideHeader}>
        {headers.map((headerGroup) => (
          <tr {...headerGroup.getHeaderGroupProps()}>
            {hRenderer(headerGroup.headers)}
          </tr>
        ))}
      </thead>
      <tbody {...tableBodyProps}>
        {emptyText && empty ? (
          <tr>
            <td colSpan={colCount} className="text-center">
              {emptyText}
            </td>
          </tr>
        ) : (
          rows.map((row) => {
            prepareRow(row);
            return rRenderer(row);
          })
        )}
      </tbody>
    </Table>
  );
}
