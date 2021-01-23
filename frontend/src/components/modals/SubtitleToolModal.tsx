import React, { FunctionComponent } from "react";
import BasicModal, { BasicModalProps } from "./BasicModal";

import { Column } from "react-table";
import { BasicTable } from "..";

interface Props {
  subtitles: Subtitle[];
}

const Table: FunctionComponent<Props> = ({ subtitles }) => {
  const columns: Column<Subtitle>[] = React.useMemo<Column<Subtitle>[]>(
    () => [
      {
        Header: "Language",
        accessor: "name",
      },
      {
        Header: "File Name",
        accessor: "path",
        Cell: (row) => {
          if (row.value !== null) {
            let idx = row.value.lastIndexOf("/") ?? -1;

            if (idx === -1) {
              idx = row.value.lastIndexOf("\\") ?? -1;
            }

            if (idx !== -1) {
              return row.value.slice(idx + 1);
            }
          }

          return row.value;
        },
      },
      {
        Header: "Tools",
        accessor: "code2",
        Cell: (row) => {
          return null;
        },
      },
    ],
    []
  );

  const data: Subtitle[] = React.useMemo<Subtitle[]>(
    () => subtitles.filter((val) => val.path !== null),
    [subtitles]
  );

  return (
    <BasicTable
      emptyText="No External Subtitles Found"
      options={{ columns, data }}
    ></BasicTable>
  );
};

const Tools: FunctionComponent<Props & BasicModalProps> = (props) => {
  return (
    <BasicModal {...props}>
      <Table {...props}></Table>
    </BasicModal>
  );
};

export default Tools;
