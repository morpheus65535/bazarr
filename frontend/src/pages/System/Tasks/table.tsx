import { faSync } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useRunTask } from "apis/hooks";
import { AsyncButton, SimpleTable } from "components";
import React, { FunctionComponent, useMemo } from "react";
import { Column, useSortBy } from "react-table";

interface Props {
  tasks: readonly System.Task[];
}

const Table: FunctionComponent<Props> = ({ tasks }) => {
  const columns: Column<System.Task>[] = useMemo<Column<System.Task>[]>(
    () => [
      {
        Header: "Name",
        accessor: "name",
        className: "text-nowrap",
      },
      {
        Header: "Interval",
        accessor: "interval",
        className: "text-nowrap",
      },
      {
        Header: "Next Execution",
        accessor: "next_run_in",
        className: "text-nowrap",
      },
      {
        accessor: "job_running",
        Cell: (row) => {
          const { job_id } = row.row.original;
          const { mutateAsync } = useRunTask();
          return (
            <AsyncButton
              promise={() => mutateAsync(job_id)}
              variant="light"
              size="sm"
              disabled={row.value}
              animation={false}
            >
              <FontAwesomeIcon icon={faSync} spin={row.value}></FontAwesomeIcon>
            </AsyncButton>
          );
        },
      },
    ],
    []
  );

  return (
    <SimpleTable
      initialState={{ sortBy: [{ id: "name", desc: false }] }}
      columns={columns}
      data={tasks}
      plugins={[useSortBy]}
    ></SimpleTable>
  );
};

export default Table;
