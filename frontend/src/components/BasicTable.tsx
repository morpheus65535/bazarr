import React from "react";
import { Table } from "react-bootstrap";
import { TableOptions, useTable } from "react-table";

export interface Props<T extends object = {}> {
  options: TableOptions<T>;
}

export default function BasicTable<T extends object = {}>(props: Props<T>) {
  const instance = useTable(props.options);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = instance;

  const header = (
    <thead>
      {headerGroups.map((headerGroup) => (
        <tr {...headerGroup.getHeaderGroupProps()}>
          {headerGroup.headers.map((col) => (
            <th {...col.getHeaderProps()}>{col.render("Header")}</th>
          ))}
        </tr>
      ))}
    </thead>
  );

  const body = (
    <tbody {...getTableBodyProps()}>
      {rows.map(
        (row): JSX.Element => {
          prepareRow(row);
          return (
            <tr {...row.getRowProps()}>
              {row.cells.map((cell) => (
                <td {...cell.getCellProps()}>{cell.render("Cell")}</td>
              ))}
            </tr>
          );
        }
      )}
    </tbody>
  );

  return (
    <Table {...getTableProps()}>
      {header}
      {body}
    </Table>
  );
}
