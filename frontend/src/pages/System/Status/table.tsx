import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { Text } from "@mantine/core";
import { SimpleTable } from "@/components";

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
          return <Text className="table-no-wrap">{value}</Text>;
        },
      },
      {
        Header: "Issue",
        accessor: "issue",
        Cell: ({ value }) => {
          return <Text className="table-primary">{value}</Text>;
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
