import { FunctionComponent, useMemo } from "react";
import { ColumnDef } from "@tanstack/react-table";
import SimpleTable from "@/components/tables/SimpleTable";

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

  return <SimpleTable columns={columns} data={props.providers}></SimpleTable>;
};

export default Table;
