import React, { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { SimpleTable } from "../../components";

interface Props {
  health: readonly System.Health[];
}

const Table: FunctionComponent<Props> = (props) => {
  const columns: Column<System.Health>[] = useMemo<Column<System.Health>[]>(
    () => [
      {
        Header: "Object",
        accessor: "object",
      },
      {
        Header: "Issue",
        accessor: "issue",
      },
    ],
    []
  );

  return <SimpleTable columns={columns} data={props.health}></SimpleTable>;
};

export default Table;
