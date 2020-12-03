import React, { FunctionComponent } from "react";
import { Badge, Button } from "react-bootstrap";
import { Column } from "react-table";

import BasicTable from "../../components/tables/BasicTable";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTrash } from "@fortawesome/free-solid-svg-icons";

interface Props {
  movie: Movie;
}

const Table: FunctionComponent<Props> = (props) => {
  const { movie } = props;

  const columns: Column<Subtitle>[] = React.useMemo<Column<Subtitle>[]>(
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
        accessor: "code2",
        Cell: (row) => {
          const { original } = row.row;
          if (original.path === null || original.path.length === 0) {
            return null;
          } else {
            return (
              <Button variant="light" size="sm">
                <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
              </Button>
            );
          }
        },
      },
    ],
    []
  );

  return <BasicTable options={{ columns, data: movie.subtitles }}></BasicTable>;
};

export default Table;
