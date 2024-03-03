import { faChevronCircleRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Box, Text } from "@mantine/core";
import {
  Cell,
  HeaderGroup,
  Row,
  useExpanded,
  useGroupBy,
  useSortBy,
} from "react-table";
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
        <tr {...row.getRowProps()}>
          <td {...cell.getCellProps()} colSpan={row.cells.length}>
            <Text {...row.getToggleRowExpandedProps()} p={2}>
              {cell.render("Cell")}
              <Box component="span" mx={12}>
                <FontAwesomeIcon
                  icon={faChevronCircleRight}
                  rotation={rotation}
                ></FontAwesomeIcon>
              </Box>
            </Text>
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
            <td {...cell.getCellProps()}>{renderCell(cell, row)}</td>
          ))}
      </tr>
    );
  }
}

function renderHeaders<T extends object>(
  headers: HeaderGroup<T>[],
): JSX.Element[] {
  return headers
    .filter((col) => !col.isGrouped)
    .map((col) => <th {...col.getHeaderProps()}>{col.render("Header")}</th>);
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
