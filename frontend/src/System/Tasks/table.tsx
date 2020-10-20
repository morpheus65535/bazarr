import React from "react";
import { Column } from "react-table";
import BasicTable from "../../components/BasicTable";

import { connect } from "react-redux";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSync } from "@fortawesome/free-solid-svg-icons";

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
        Header: "",
        id: "tasks-action",
        Cell: () => {
          return <FontAwesomeIcon icon={faSync}></FontAwesomeIcon>;
        },
      },
    ],
    []
  );

  return <BasicTable options={{ columns, data: props.tasks }}></BasicTable>;
}

export default connect(mapStateToProps)(Table);
