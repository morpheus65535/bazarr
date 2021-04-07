import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Column } from "react-table";
import { MoviesApi } from "../../apis";
import { AsyncButton, LanguageText, SimpleTable } from "../../components";

const missingText = "Missing Subtitles";

interface Props {
  movie: Item.Movie;
}

const Table: FunctionComponent<Props> = (props) => {
  const { movie } = props;

  const columns: Column<Subtitle>[] = useMemo<Column<Subtitle>[]>(
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
        Cell: ({ row }) => {
          if (row.original.path === missingText) {
            return (
              <Badge variant="primary">
                <LanguageText text={row.original} long></LanguageText>
              </Badge>
            );
          } else {
            return (
              <Badge variant="secondary">
                <LanguageText text={row.original} long></LanguageText>
              </Badge>
            );
          }
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
              <AsyncButton
                promise={() =>
                  MoviesApi.downloadSubtitles(movie.radarrId, {
                    language: original.code2,
                    hi: original.hi,
                    forced: original.forced,
                  })
                }
                variant="light"
                size="sm"
              >
                <FontAwesomeIcon icon={faSearch}></FontAwesomeIcon>
              </AsyncButton>
            );
          } else {
            return (
              <AsyncButton
                variant="light"
                size="sm"
                promise={() =>
                  MoviesApi.deleteSubtitles(movie.radarrId, {
                    language: original.code2,
                    hi: original.hi,
                    forced: original.forced,
                    path: original.path ?? "",
                  })
                }
              >
                <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
              </AsyncButton>
            );
          }
        },
      },
    ],
    [movie]
  );

  const data: Subtitle[] = useMemo(() => {
    const missing = movie.missing_subtitles.map((item) => {
      item.path = missingText;
      return item;
    });

    return movie.subtitles.concat(missing);
  }, [movie.missing_subtitles, movie.subtitles]);

  return (
    <SimpleTable
      columns={columns}
      data={data}
      emptyText="No Subtitles Found For This Movie"
    ></SimpleTable>
  );
};

export default Table;
