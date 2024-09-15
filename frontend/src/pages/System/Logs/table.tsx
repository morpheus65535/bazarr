import { FunctionComponent, useMemo } from "react";
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
import { ColumnDef } from "@tanstack/react-table";
import { Action } from "@/components";
import PageTable from "@/components/tables/PageTable";
import { useModals } from "@/modules/modals";
import SystemLogModal from "./modal";

interface Props {
  logs: System.Log[];
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
  const modals = useModals();

  const columns = useMemo<ColumnDef<System.Log>[]>(
    () => [
      {
        accessorKey: "type",
        cell: ({
          row: {
            original: { type },
          },
        }) => <FontAwesomeIcon icon={mapTypeToIcon(type)}></FontAwesomeIcon>,
      },
      {
        Header: "Message",
        accessorKey: "message",
      },
      {
        Header: "Date",
        accessorKey: "timestamp",
      },
      {
        accessorKey: "exception",
        cell: ({
          row: {
            original: { exception },
          },
        }) => {
          if (exception) {
            return (
              <Action
                label="Detail"
                icon={faLayerGroup}
                onClick={() =>
                  modals.openContextModal(SystemLogModal, { stack: exception })
                }
              ></Action>
            );
          } else {
            return null;
          }
        },
      },
    ],
    [modals],
  );

  return (
    <>
      <PageTable columns={columns} data={logs}></PageTable>
    </>
  );
};

export default Table;
