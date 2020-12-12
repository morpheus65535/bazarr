import React, { FunctionComponent } from "react";
import BasicModal, { ModalProps } from "./BasicModal";

import { Column } from "react-table";
import { BasicTable } from "../../components";

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
        // TODO: (Backend) Change to Filename
        Header: "File Name",
        accessor: "path",
      },
      {
        Header: "Tools",
        accessor: "code3",
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

  return <BasicTable options={{ columns, data }}></BasicTable>;
};

const Tools: FunctionComponent<Props & ModalProps> = (props) => {
  return (
    <BasicModal {...props}>
      <Table {...props}></Table>
    </BasicModal>
  );
};

export default Tools;
