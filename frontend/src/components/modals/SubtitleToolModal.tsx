import React, { FunctionComponent, useMemo } from "react";
import BasicModal, { BasicModalProps } from "./BasicModal";

import { Column } from "react-table";
import { BasicTable } from "..";
import { usePayload } from "./provider";

interface Props {}

const Table: FunctionComponent<Props> = () => {
  const episode = usePayload<Episode>();

  const columns: Column<Subtitle>[] = useMemo<Column<Subtitle>[]>(
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

  const data: Subtitle[] = useMemo<Subtitle[]>(
    () => episode?.subtitles.filter((val) => val.path !== null) ?? [],
    [episode]
  );

  return (
    <BasicTable
      emptyText="No External Subtitles Found"
      columns={columns}
      data={data}
    ></BasicTable>
  );
};

const Tools: FunctionComponent<Props & BasicModalProps> = (props) => {
  const episode = usePayload<Episode>();
  return (
    <BasicModal title={`Tools - ${episode?.title ?? ""}`} {...props}>
      <Table {...props}></Table>
    </BasicModal>
  );
};

export default Tools;
