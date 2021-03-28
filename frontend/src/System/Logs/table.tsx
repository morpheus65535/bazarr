import { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import {
  faBug,
  faCode,
  faExclamationCircle,
  faInfoCircle,
  faLayerGroup,
  faQuestion,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { isUndefined } from "lodash";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Column, Row } from "react-table";
import { ActionButton, PageTable, useShowModal } from "../../components";
import SystemLogModal from "./modal";

interface Props {
  logs: readonly System.Log[];
}

function mapTypeToIcon(type: System.LogType): IconDefinition {
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

const Table: FunctionComponent<Props> = ({ logs }) => {
  const showModal = useShowModal();
  const show = useCallback(
    (row: Row<System.Log>, text: string) =>
      showModal<string>("system-log", text),
    [showModal]
  );
  const columns: Column<System.Log>[] = useMemo<Column<System.Log>[]>(
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
        Header: "Date",
        accessor: "timestamp",
        className: "text-nowrap",
      },
      {
        accessor: "exception",
        Cell: ({ row, value, externalUpdate }) => {
          if (!isUndefined(value)) {
            return (
              <ActionButton
                icon={faLayerGroup}
                onClick={() => externalUpdate && externalUpdate(row, value)}
              ></ActionButton>
            );
          } else {
            return null;
          }
        },
      },
    ],
    []
  );

  return (
    <React.Fragment>
      <PageTable
        columns={columns}
        data={logs}
        externalUpdate={show}
      ></PageTable>
      <SystemLogModal size="xl" modalKey="system-log"></SystemLogModal>
    </React.Fragment>
  );
};

export default Table;
