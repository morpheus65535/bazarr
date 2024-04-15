import { useIsLoading } from "@/contexts";
import { usePageSize } from "@/utilities/storage";
import { Box, createStyles, Skeleton, Table, Text } from "@mantine/core";
import { ReactNode, useMemo } from "react";
import { HeaderGroup, Row, TableInstance } from "react-table";

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

const useStyles = createStyles((theme) => {
  return {
    container: {
      display: "block",
      maxWidth: "100%",
      overflowX: "auto",
      overflowWrap: "anywhere",
    },
    table: {
      borderCollapse: "collapse",
    },
    header: {},
  };
});

function DefaultHeaderRenderer<T extends object>(
  headers: HeaderGroup<T>[],
): JSX.Element[] {
  return headers.map((col) => (
    <th style={{ whiteSpace: "nowrap" }} {...col.getHeaderProps()}>
      {col.render("Header")}
    </th>
  ));
}

function DefaultRowRenderer<T extends object>(row: Row<T>): JSX.Element | null {
  return (
    <tr {...row.getRowProps()}>
      {row.cells.map((cell) => (
        <td {...cell.getCellProps()}>{cell.render("Cell")}</td>
      ))}
    </tr>
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

  const { classes } = useStyles();

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
        <tr key={i}>
          <td colSpan={colCount}>
            <Skeleton height={24}></Skeleton>
          </td>
        </tr>
      ));
  } else if (empty && tableStyles?.emptyText) {
    body = (
      <tr>
        <td colSpan={colCount}>
          <Text align="center">{tableStyles.emptyText}</Text>
        </td>
      </tr>
    );
  } else {
    body = rows.map((row) => {
      prepareRow(row);
      return rowRenderer(row);
    });
  }

  return (
    <Box className={classes.container}>
      <Table
        className={classes.table}
        striped={tableStyles?.striped ?? true}
        {...getTableProps()}
      >
        <thead className={classes.header} hidden={tableStyles?.hideHeader}>
          {headerGroups.map((headerGroup) => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headersRenderer(headerGroup.headers)}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>{body}</tbody>
      </Table>
    </Box>
  );
}
