import { faChevronCircleRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React from "react";
import {
  Cell,
  HeaderGroup,
  Row,
  TableOptions,
  useExpanded,
  useGroupBy,
  useSortBy,
} from "react-table";
import { TableStyleProps } from "./BaseTable";
import SimpleTable from "./SimpleTable";

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

function renderHeaders<T extends object>(
  headers: HeaderGroup<T>[]
): JSX.Element[] {
  return headers
    .filter((col) => !col.isGrouped)
    .map((col) => <th {...col.getHeaderProps()}>{col.render("Header")}</th>);
}

type Props<T extends object> = TableOptions<T> & TableStyleProps<T>;

function GroupTable<T extends object = {}>(props: Props<T>) {
  const plugins = [useGroupBy, useSortBy, useExpanded];
  return (
    <SimpleTable
      {...props}
      plugins={plugins}
      headersRenderer={renderHeaders}
      rowRenderer={renderRow}
    ></SimpleTable>
  );
}

export default GroupTable;
