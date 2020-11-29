import React, { FunctionComponent } from "react";
import { Badge, Button } from "react-bootstrap";
import { Column } from "react-table";

import BasicTable from "../../components/BasicTable";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTimes } from "@fortawesome/free-solid-svg-icons";

interface Props {
  movie: Movie;
}

const Table: FunctionComponent<Props> = (props) => {
  const { movie } = props;

  const columns: Column<SubtitleInfo>[] = React.useMemo<Column<SubtitleInfo>[]>(
    () => [
      {
        Header: "Subtitle Path",
        accessor: "path",
        Cell: (row) => {
          if (row.value === null || row.value.length === 0) {
            return "Video File Subtitle Track";
          } else {
            return row.value;
          }
        },
      },
      {
        Header: "Language",
        accessor: "name",
        Cell: (row) => {
          return <Badge variant="secondary">{row.value}</Badge>;
        },
      },
      {
        Header: "",
        accessor: "code2",
        Cell: (row) => {
          return (
            <Button variant="light" size="sm">
              <FontAwesomeIcon icon={faTimes}></FontAwesomeIcon>
            </Button>
          );
        },
      },
    ],
    []
  );

  return <BasicTable options={{ columns, data: movie.subtitles }}></BasicTable>;
};

export default Table;
