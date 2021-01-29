import React, { useMemo } from "react";
import { Table } from "react-bootstrap";
import {
  TableOptions,
  useGroupBy,
  useExpanded,
  useSortBy,
  useTable,
  Cell,
  Row,
} from "react-table";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faChevronCircleRight } from "@fortawesome/free-solid-svg-icons";

function renderCell<T extends object = {}>(cell: Cell<T, any>, row: Row<T>) {
  if (cell.isGrouped) {
    return (
      <span {...row.getToggleRowExpandedProps()}>{cell.render("Cell")}</span>
    );
  } else if (row.canExpand || cell.isAggregated) {
    return null;
  } else {
    return cell.render("Cell");
  }
}

function renderRow<T extends object>(row: Row<T>) {
  if (row.canExpand) {
    const cell = row.cells.find((cell) => cell.isGrouped);
    if (cell) {
      const rotation = row.isExpanded ? 90 : undefined;
      return (
        <tr {...row.getRowProps()}>
          <td
            className="p-0"
            {...cell.getCellProps()}
            colSpan={row.cells.length}
          >
            <span
              {...row.getToggleRowExpandedProps()}
              className="d-flex align-items-center p-2"
            >
              {cell.render("Cell")}
              <FontAwesomeIcon
                className="mx-2"
                icon={faChevronCircleRight}
                rotation={rotation}
              ></FontAwesomeIcon>
            </span>
          </td>
        </tr>
      );
    } else {
      return null;
    }
  } else {
    return (
      <tr {...row.getRowProps()}>
        {row.cells
          .filter((cell) => !cell.isPlaceholder)
          .map((cell) => (
            <td className={cell.column.className} {...cell.getCellProps()}>
              {renderCell(cell, row)}
            </td>
          ))}
      </tr>
    );
  }
}

interface Props<T extends object = {}> extends TableOptions<T> {
  emptyText?: string;
}

export default function BasicTable<T extends object = {}>(props: Props<T>) {
  const { emptyText, ...options } = props;
  const instance = useTable(options, useGroupBy, useSortBy, useExpanded);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = instance;

  const header = useMemo(
    () => (
      <thead>
        {headerGroups.map((headerGroup) => (
          <tr {...headerGroup.getHeaderGroupProps()}>
            {headerGroup.headers
              .filter((col) => !col.isGrouped)
              .map((col) => (
                <th {...col.getHeaderProps()}>{col.render("Header")}</th>
              ))}
          </tr>
        ))}
      </thead>
    ),
    [headerGroups]
  );

  const colCount = useMemo(() => {
    return headerGroups.reduce(
      (prev, curr) => (curr.headers.length > prev ? curr.headers.length : prev),
      0
    );
  }, [headerGroups]);

  const empty = rows.length === 0;

  const body = useMemo(
    () => (
      <tbody {...getTableBodyProps()}>
        {emptyText && empty ? (
          <tr>
            <td colSpan={colCount} className="text-center">
              {emptyText}
            </td>
          </tr>
        ) : (
          rows.map((row) => {
            prepareRow(row);
            return renderRow(row);
          })
        )}
      </tbody>
    ),
    [getTableBodyProps, prepareRow, rows, colCount, empty, emptyText]
  );

  return (
    <React.Fragment>
      <Table striped borderless responsive {...getTableProps()}>
        {header}
        {body}
      </Table>
    </React.Fragment>
  );
}
