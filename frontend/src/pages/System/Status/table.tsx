import { FunctionComponent, useMemo } from "react";
import { Text } from "@mantine/core";
import { ColumnDef } from "@tanstack/react-table";
import NewSimpleTable from "@/components/tables/NewSimpleTable";

interface Props {
  health: System.Health[];
}

const Table: FunctionComponent<Props> = ({ health }) => {
  const columns = useMemo<ColumnDef<System.Health>[]>(
    () => [
      {
        header: "Object",
        accessorKey: "object",
        cell: ({
          row: {
            original: { object },
          },
        }) => {
          return <Text className="table-no-wrap">{object}</Text>;
        },
      },
      {
        header: "Issue",
        accessorKey: "issue",
        cell: ({
          row: {
            original: { issue },
          },
        }) => {
          return <Text className="table-primary">{issue}</Text>;
        },
      },
    ],
    [],
  );

  return (
    <NewSimpleTable
      columns={columns}
      data={health}
      tableStyles={{ emptyText: "No issues with your configuration" }}
    ></NewSimpleTable>
  );
};

export default Table;
