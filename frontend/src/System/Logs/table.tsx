import React, { FunctionComponent, useMemo } from "react";
import { connect } from "react-redux";
import { Column } from "react-table";

import { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faInfoCircle,
  faExclamationCircle,
  faBug,
  faCode,
  faQuestion,
} from "@fortawesome/free-solid-svg-icons";

import { BasicTable } from "../../components";

interface Props {
  providers: SystemLog[];
}

function mapStateToProps({ system }: StoreState) {
  const { logs } = system;
  return {
    providers: logs.items,
  };
}

function mapTypeToIcon(type: SystemLogType): IconDefinition {
  switch (type) {
    case "DEBUG":
      return faCode;
    case "ERROR":
      return faBug;
    case "INFO":
      return faInfoCircle;
    case "WARNING":
      return faExclamationCircle;
    default:
      return faQuestion;
  }
}

function mapDateToString(ts: string): string {
  // TODO: Format Date
  return ts;
}

const Table: FunctionComponent<Props> = (props) => {
  const columns: Column<SystemLog>[] = useMemo<Column<SystemLog>[]>(
    () => [
      {
        accessor: "type",
        Cell: (row) => (
          <FontAwesomeIcon icon={mapTypeToIcon(row.value)}></FontAwesomeIcon>
        ),
      },
      {
        Header: "Message",
        accessor: "message",
      },
      {
        Header: "Time",
        accessor: "timestamp",
        Cell: (row) => mapDateToString(row.value),
      },
    ],
    []
  );

  return <BasicTable columns={columns} data={props.providers}></BasicTable>;
};

export default connect(mapStateToProps)(Table);
