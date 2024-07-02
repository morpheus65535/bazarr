import { ReactNode, useMemo } from "react";
import { HeaderGroup, Row, TableInstance } from "react-table";
import { Box, Skeleton, Table, Text } from "@mantine/core";
import { useIsLoading } from "@/contexts";
import { usePageSize } from "@/utilities/storage";
import styles from "./BaseTable.module.scss";

export type BaseTableProps<T extends object> = TableInstance<T> & {
  tableStyles?: TableStyleProps<T>;
};

export interface TableStyleProps<T extends object> {
  emptyText?: string;
  striped?: boolean;
  placeholder?: number;
  hideHeader?: boolean;
  fixHeader?: boolean;
  headersRenderer?: (headers: HeaderGroup<T>[]) => JSX.Element[];
  rowRenderer?: (row: Row<T>) => Nullable<JSX.Element>;
}

function DefaultHeaderRenderer<T extends object>(
  headers: HeaderGroup<T>[],
): JSX.Element[] {
  return headers.map((col) => (
    <Table.Th style={{ whiteSpace: "nowrap" }} {...col.getHeaderProps()}>
      {col.render("Header")}
    </Table.Th>
  ));
}

function DefaultRowRenderer<T extends object>(row: Row<T>): JSX.Element | null {
  return (
    <Table.Tr {...row.getRowProps()}>
      {row.cells.map((cell) => (
        <Table.Td {...cell.getCellProps()}>{cell.render("Cell")}</Table.Td>
      ))}
    </Table.Tr>
  );
}

export default function BaseTable<T extends object>(props: BaseTableProps<T>) {
  const {
    headerGroups,
    rows: tableRows,
    page: tablePages,
    prepareRow,
    getTableProps,
    getTableBodyProps,
    tableStyles,
  } = props;

  const headersRenderer = tableStyles?.headersRenderer ?? DefaultHeaderRenderer;
  const rowRenderer = tableStyles?.rowRenderer ?? DefaultRowRenderer;

  const colCount = useMemo(() => {
    return headerGroups.reduce(
      (prev, curr) => (curr.headers.length > prev ? curr.headers.length : prev),
      0,
    );
  }, [headerGroups]);

  // Switch to usePagination plugin if enabled
  const rows = tablePages ?? tableRows;

  const empty = rows.length === 0;

  const pageSize = usePageSize();
  const isLoading = useIsLoading();

  let body: ReactNode;
  if (isLoading) {
    body = Array(tableStyles?.placeholder ?? pageSize)
      .fill(0)
      .map((_, i) => (
        <Table.Tr key={i}>
          <Table.Td colSpan={colCount}>
            <Skeleton height={24}></Skeleton>
          </Table.Td>
        </Table.Tr>
      ));
  } else if (empty && tableStyles?.emptyText) {
    body = (
      <Table.Tr>
        <Table.Td colSpan={colCount}>
          <Text ta="center">{tableStyles.emptyText}</Text>
        </Table.Td>
      </Table.Tr>
    );
  } else {
    body = rows.map((row) => {
      prepareRow(row);
      return rowRenderer(row);
    });
  }

  return (
    <Box className={styles.container}>
      <Table
        className={styles.table}
        striped={tableStyles?.striped ?? true}
        {...getTableProps()}
      >
        <Table.Thead hidden={tableStyles?.hideHeader}>
          {headerGroups.map((headerGroup) => (
            <Table.Tr {...headerGroup.getHeaderGroupProps()}>
              {headersRenderer(headerGroup.headers)}
            </Table.Tr>
          ))}
        </Table.Thead>
        <Table.Tbody {...getTableBodyProps()}>{body}</Table.Tbody>
      </Table>
    </Box>
  );
}
