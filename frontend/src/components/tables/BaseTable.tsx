import React, { ReactNode, useMemo } from "react";
import { Box, Skeleton, Table, Text } from "@mantine/core";
import {
  flexRender,
  Header,
  Row,
  Table as TableInstance,
} from "@tanstack/react-table";
import { useIsLoading } from "@/contexts";
import { usePageSize } from "@/utilities/storage";
import styles from "@/components/tables/BaseTable.module.scss";

export type BaseTableProps<T extends object> = {
  instance: TableInstance<T>;
  tableStyles?: TableStyleProps<T>;
};

export interface TableStyleProps<T extends object> {
  emptyText?: string;
  striped?: boolean;
  placeholder?: number;
  hideHeader?: boolean;
  fixHeader?: boolean;
  headersRenderer?: (headers: Header<T, unknown>[]) => React.JSX.Element[];
  rowRenderer?: (row: Row<T>) => Nullable<React.JSX.Element>;
}

function DefaultHeaderRenderer<T extends object>(
  headers: Header<T, unknown>[],
): React.JSX.Element[] {
  return headers.map((header) => (
    <Table.Th style={{ whiteSpace: "nowrap" }} key={header.id}>
      {flexRender(header.column.columnDef.header, header.getContext())}
    </Table.Th>
  ));
}

function DefaultRowRenderer<T extends object>(
  row: Row<T>,
): React.JSX.Element | null {
  return (
    <Table.Tr key={row.id}>
      {row.getVisibleCells().map((cell) => (
        <Table.Td key={cell.id}>
          {flexRender(cell.column.columnDef.cell, cell.getContext())}
        </Table.Td>
      ))}
    </Table.Tr>
  );
}

export default function BaseTable<T extends object>(props: BaseTableProps<T>) {
  const { instance, tableStyles } = props;

  const headersRenderer = tableStyles?.headersRenderer ?? DefaultHeaderRenderer;
  const rowRenderer = tableStyles?.rowRenderer ?? DefaultRowRenderer;

  const colCount = useMemo(() => {
    return instance
      .getHeaderGroups()
      .reduce(
        (prev, curr) =>
          curr.headers.length > prev ? curr.headers.length : prev,
        0,
      );
  }, [instance]);

  const empty = instance.getRowCount() === 0;

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
    body = instance.getRowModel().rows.map((row) => {
      return rowRenderer(row);
    });
  }

  return (
    <Box className={styles.container}>
      <Table
        className={styles.table}
        highlightOnHover
        striped={tableStyles?.striped ?? true}
      >
        <Table.Thead hidden={tableStyles?.hideHeader}>
          {instance.getHeaderGroups().map((headerGroup) => (
            <Table.Tr key={headerGroup.id}>
              {headersRenderer(headerGroup.headers)}
            </Table.Tr>
          ))}
        </Table.Thead>
        <Table.Tbody>{body}</Table.Tbody>
      </Table>
    </Box>
  );
}
