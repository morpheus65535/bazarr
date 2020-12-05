import React, { FunctionComponent } from "react";
import { Badge, Button } from "react-bootstrap";
import { Column } from "react-table";

import { BasicTable } from "../../components";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";

const missingText = "Missing";

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
          } else if (row.value === missingText) {
            return <span className="text-muted">{row.value}</span>;
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
          } else if (original.path === missingText) {
            return (
              <Button variant="light" size="sm">
                <FontAwesomeIcon icon={faSearch}></FontAwesomeIcon>
              </Button>
            );
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

  const data: Subtitle[] = React.useMemo(() => {
    const missing = movie.missing_subtitles.map((item) => {
      item.path = missingText;
      return item;
    });

    return movie.subtitles.concat(missing);
  }, [movie.missing_subtitles, movie.subtitles]);

  return <BasicTable options={{ columns, data }}></BasicTable>;
};

export default Table;
