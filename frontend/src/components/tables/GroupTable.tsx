import React from "react";
import { Box, Table, Text } from "@mantine/core";
import { faChevronCircleRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Cell,
  flexRender,
  getExpandedRowModel,
  getGroupedRowModel,
  Header,
  Row,
} from "@tanstack/react-table";
import NewSimpleTable, {
  NewSimpleTableProps,
} from "@/components/tables/NewSimpleTable";

function renderCell<T extends object = object>(
  cell: Cell<T, unknown>,
  row: Row<T>,
) {
  if (cell.getIsGrouped()) {
    return (
      <div>{flexRender(cell.column.columnDef.cell, cell.getContext())}</div>
    );
  } else if (row.getCanExpand() || cell.getIsAggregated()) {
    return null;
  } else {
    return flexRender(cell.column.columnDef.cell, cell.getContext());
  }
}

function renderRow<T extends object>(row: Row<T>) {
  if (row.getCanExpand()) {
    const cell = row.getVisibleCells().find((cell) => cell.getIsGrouped());

    if (cell) {
      const rotation = row.getIsExpanded() ? 90 : undefined;

      return (
        <Table.Tr key={row.id} style={{ cursor: "pointer" }}>
          <Table.Td key={cell.id} colSpan={row.getVisibleCells().length}>
            <Text p={2} onClick={() => row.toggleExpanded()}>
              {flexRender(cell.column.columnDef.cell, cell.getContext())}
              <Box component="span" mx={12}>
                <FontAwesomeIcon
                  icon={faChevronCircleRight}
                  rotation={rotation}
                ></FontAwesomeIcon>
              </Box>
            </Text>
          </Table.Td>
        </Table.Tr>
      );
    } else {
      return null;
    }
  } else {
    return (
      <Table.Tr key={row.id}>
        {row
          .getVisibleCells()
          .filter((cell) => !cell.getIsPlaceholder())
          .map((cell) => (
            <Table.Td key={cell.id}>{renderCell(cell, row)}</Table.Td>
          ))}
      </Table.Tr>
    );
  }
}

function renderHeaders<T extends object>(
  headers: Header<T, unknown>[],
): React.JSX.Element[] {
  return headers.map((header) => (
    <Table.Th key={header.id}>
      {flexRender(header.column.columnDef.header, header.getContext())}
    </Table.Th>
  ));
}

type Props<T extends object> = Omit<
  NewSimpleTableProps<T>,
  "headersRenderer" | "rowRenderer"
>;

function GroupTable<T extends object = object>(props: Props<T>) {
  return (
    <NewSimpleTable
      {...props}
      enableGrouping
      enableExpanding
      getGroupedRowModel={getGroupedRowModel()}
      getExpandedRowModel={getExpandedRowModel()}
      tableStyles={{ headersRenderer: renderHeaders, rowRenderer: renderRow }}
    ></NewSimpleTable>
  );
}

export default GroupTable;
