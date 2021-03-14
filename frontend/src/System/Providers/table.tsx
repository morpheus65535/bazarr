import React, { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { SimpleTable } from "../../components";

interface Props {
  providers: readonly System.Provider[];
}

const Table: FunctionComponent<Props> = (props) => {
  const columns: Column<System.Provider>[] = useMemo<Column<System.Provider>[]>(
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

  return <SimpleTable columns={columns} data={props.providers}></SimpleTable>;
};

export default Table;
