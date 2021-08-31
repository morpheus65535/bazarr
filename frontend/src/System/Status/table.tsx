import React, { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { SimpleTable } from "../../components";

interface Props {
  health: readonly System.Health[];
}

const Table: FunctionComponent<Props> = ({ health }) => {
  const columns: Column<System.Health>[] = useMemo<Column<System.Health>[]>(
    () => [
      {
        Header: "Object",
        accessor: "object",
      },
      {
        Header: "Issue",
        accessor: "issue",
        className: "status-issue",
      },
    ],
    []
  );

  return (
    <SimpleTable
      responsive
      columns={columns}
      data={health}
      emptyText="No issues with your configuration"
    ></SimpleTable>
  );
};

export default Table;
