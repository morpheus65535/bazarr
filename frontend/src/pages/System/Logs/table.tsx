import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
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
import { Action, PageTable } from "@/components";
import { useModals } from "@/modules/modals";
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
      },
      {
        accessor: "exception",
        Cell: ({ value }) => {
          const modals = useModals();
          if (value) {
            return (
              <Action
                label="Detail"
                icon={faLayerGroup}
                onClick={() =>
                  modals.openContextModal(SystemLogModal, { stack: value })
                }
              ></Action>
            );
          } else {
            return null;
          }
        },
      },
    ],
    [],
  );

  return (
    <>
      <PageTable columns={columns} data={logs}></PageTable>
    </>
  );
};

export default Table;
