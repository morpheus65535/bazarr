import { SimpleTable } from "@/components";
import { useTableStyles } from "@/styles";
import { Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";

interface Props {
  health: readonly System.Health[];
}

const Table: FunctionComponent<Props> = ({ health }) => {
  const columns: Column<System.Health>[] = useMemo<Column<System.Health>[]>(
    () => [
      {
        Header: "Object",
        accessor: "object",
        Cell: ({ value }) => {
          const { classes } = useTableStyles();
          return <Text className={classes.noWrap}>{value}</Text>;
        },
      },
      {
        Header: "Issue",
        accessor: "issue",
        Cell: ({ value }) => {
          const { classes } = useTableStyles();
          return <Text className={classes.primary}>{value}</Text>;
        },
      },
    ],
    [],
  );

  return (
    <SimpleTable
      columns={columns}
      data={health}
      tableStyles={{ emptyText: "No issues with your configuration" }}
    ></SimpleTable>
  );
};

export default Table;
