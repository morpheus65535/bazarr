import React from "react";
import { Column } from "react-table";
import { BasicTable } from "../../components";
import { ExecSystemTask } from "../../@redux/actions/system";

import { connect } from "react-redux";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSync } from "@fortawesome/free-solid-svg-icons";
import { Button } from "react-bootstrap";

interface Props {
  tasks: Array<SystemTaskResult>;
  exec: (id: string) => void;
}

function mapStateToProps({ system }: StoreState) {
  const { tasks } = system;
  return {
    tasks: tasks.items,
  };
}

function Table(props: Props) {
  const { exec } = props;

  const columns: Column<SystemTaskResult>[] = React.useMemo<
    Column<SystemTaskResult>[]
  >(
    () => [
      {
        Header: "Name",
        accessor: "name",
      },
      {
        Header: "Execution Frequency",
        accessor: "interval",
      },
      {
        Header: "Next Execution",
        accessor: "next_run_in",
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
                onClick={() => exec(job_id)}
              ></FontAwesomeIcon>
            </Button>
          );
        },
      },
    ],
    [exec]
  );

  return <BasicTable options={{ columns, data: props.tasks }}></BasicTable>;
}

export default connect(mapStateToProps, {
  exec: ExecSystemTask,
})(Table);
