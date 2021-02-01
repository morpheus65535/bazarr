import { faSync } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { useMemo } from "react";
import { Button } from "react-bootstrap";
import { connect } from "react-redux";
import { Column } from "react-table";
import { SystemApi } from "../../apis";
import { BasicTable } from "../../components";

interface Props {
  tasks: Array<SystemTaskResult>;
}

function mapStateToProps({ system }: StoreState) {
  const { tasks } = system;
  return {
    tasks: tasks.items,
  };
}

function Table(props: Props) {
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
            <Button variant="light" size="sm" disabled={row.value}>
              <FontAwesomeIcon
                icon={faSync}
                spin={row.value}
                onClick={() => SystemApi.execTasks(job_id)}
              ></FontAwesomeIcon>
            </Button>
          );
        },
      },
    ],
    []
  );

  return <BasicTable columns={columns} data={props.tasks}></BasicTable>;
}

export default connect(mapStateToProps)(Table);
