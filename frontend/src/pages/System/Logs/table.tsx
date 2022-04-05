import { ActionIcon, PageTable } from "@/components";
import { useModalControl } from "@/modules/modals";
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
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
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
        className: "text-nowrap",
      },
      {
        accessor: "exception",
        Cell: ({ value }) => {
          const { show } = useModalControl();
          if (!isUndefined(value)) {
            return (
              <ActionIcon
                icon={faLayerGroup}
                onClick={() => show(SystemLogModal, value)}
              ></ActionIcon>
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
    <>
      <PageTable columns={columns} data={logs}></PageTable>
      <SystemLogModal></SystemLogModal>
    </>
  );
};

export default Table;
