import { faSync } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { connect } from "react-redux";
import { Column } from "react-table";
import { systemRunTasks } from "../../@redux/actions";
import { SystemApi } from "../../apis";
import { AsyncButton, BasicTable } from "../../components";

interface Props {
  tasks: Array<SystemTaskResult>;
  run: (id: string) => void;
}

function mapStateToProps({ system }: StoreState) {
  const { tasks } = system;
  return {
    tasks: tasks.items,
  };
}

const Table: FunctionComponent<Props> = ({ tasks, run }) => {
  const columns: Column<SystemTaskResult>[] = useMemo<
    Column<SystemTaskResult>[]
  >(
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
            >
              <FontAwesomeIcon icon={faSync} spin={row.value}></FontAwesomeIcon>
            </AsyncButton>
          );
        },
      },
    ],
    []
  );

  return <BasicTable columns={columns} data={tasks}></BasicTable>;
};

export default connect(mapStateToProps, { run: systemRunTasks })(Table);
