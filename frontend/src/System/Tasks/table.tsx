import { faSync } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { systemRunTasks } from "../../@redux/actions";
import { useReduxAction } from "../../@redux/hooks/base";
import { SystemApi } from "../../apis";
import { AsyncButton, SimpleTable } from "../../components";

interface Props {
  tasks: readonly System.Task[];
}

const Table: FunctionComponent<Props> = ({ tasks }) => {
  const run = useReduxAction(systemRunTasks);
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
          return (
            <AsyncButton
              promise={() => SystemApi.runTask(job_id)}
              onSuccess={() => run(job_id)}
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
    [run]
  );

  return <SimpleTable columns={columns} data={tasks}></SimpleTable>;
};

export default Table;
