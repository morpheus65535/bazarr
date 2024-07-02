import { FunctionComponent, useMemo } from "react";
import { ColumnDef } from "@tanstack/react-table";
import NewSimpleTable from "@/components/tables/NewSimpleTable";

interface Props {
  providers: System.Provider[];
}

const Table: FunctionComponent<Props> = (props) => {
  const columns = useMemo<ColumnDef<System.Provider>[]>(
    () => [
      {
        header: "Name",
        accessorKey: "name",
      },
      {
        header: "Status",
        accessorKey: "status",
      },
      {
        header: "Next Retry",
        accessorKey: "retry",
      },
    ],
    [],
  );

  return (
    <NewSimpleTable columns={columns} data={props.providers}></NewSimpleTable>
  );
};

export default Table;
