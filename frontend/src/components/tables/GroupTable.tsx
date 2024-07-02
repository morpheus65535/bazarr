import {
  Cell,
  HeaderGroup,
  Row,
  useExpanded,
  useGroupBy,
  useSortBy,
} from "react-table";
import { Box, Table, Text } from "@mantine/core";
import { faChevronCircleRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import SimpleTable, { SimpleTableProps } from "./SimpleTable";

function renderCell<T extends object = object>(cell: Cell<T>, row: Row<T>) {
  if (cell.isGrouped) {
    return (
      <div {...row.getToggleRowExpandedProps()}>{cell.render("Cell")}</div>
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
        <Table.Tr {...row.getRowProps()}>
          <Table.Td {...cell.getCellProps()} colSpan={row.cells.length}>
            <Text {...row.getToggleRowExpandedProps()} p={2}>
              {cell.render("Cell")}
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
      <Table.Tr {...row.getRowProps()}>
        {row.cells
          .filter((cell) => !cell.isPlaceholder)
          .map((cell) => (
            <Table.Td {...cell.getCellProps()}>
              {renderCell(cell, row)}
            </Table.Td>
          ))}
      </Table.Tr>
    );
  }
}

function renderHeaders<T extends object>(
  headers: HeaderGroup<T>[],
): JSX.Element[] {
  return headers
    .filter((col) => !col.isGrouped)
    .map((col) => (
      <Table.Th {...col.getHeaderProps()}>{col.render("Header")}</Table.Th>
    ));
}

type Props<T extends object> = Omit<
  SimpleTableProps<T>,
  "plugins" | "headersRenderer" | "rowRenderer"
>;

const plugins = [useGroupBy, useSortBy, useExpanded];

function GroupTable<T extends object = object>(props: Props<T>) {
  return (
    <SimpleTable
      {...props}
      plugins={plugins}
      tableStyles={{ headersRenderer: renderHeaders, rowRenderer: renderRow }}
    ></SimpleTable>
  );
}

export default GroupTable;
