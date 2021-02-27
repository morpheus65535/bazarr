import React, { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { BaseTable } from "../../components";

interface Props {
  providers: SystemProvider[];
}

const Table: FunctionComponent<Props> = (props) => {
  const columns: Column<SystemProvider>[] = useMemo<Column<SystemProvider>[]>(
    () => [
      {
        Header: "Name",
        accessor: "name",
      },
      {
        Header: "Status",
        accessor: "status",
      },
      {
        Header: "Next Retry",
        accessor: "retry",
      },
    ],
    []
  );

  return <BaseTable columns={columns} data={props.providers}></BaseTable>;
};

export default Table;
