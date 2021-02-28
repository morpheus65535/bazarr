import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { connect } from "react-redux";
import { Column } from "react-table";
import { movieUpdateInfoAll } from "../../@redux/actions";
import { MoviesApi } from "../../apis";
import { AsyncButton, SimpleTable, SubtitleText } from "../../components";

const missingText = "Subtitle Missing";

interface Props {
  movie: Movie;
  update: (id: number) => void;
}

const Table: FunctionComponent<Props> = (props) => {
  const { movie, update } = props;

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
          return (
            <Badge variant="secondary">
              <SubtitleText name subtitle={row.original}></SubtitleText>
            </Badge>
          );
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
                onSuccess={() => update(movie.radarrId)}
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
                onSuccess={() => update(movie.radarrId)}
              >
                <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
              </AsyncButton>
            );
          }
        },
      },
    ],
    [movie, update]
  );

  const data: Subtitle[] = useMemo(() => {
    const missing = movie.missing_subtitles.map((item) => {
      item.path = missingText;
      return item;
    });

    return movie.subtitles.concat(missing);
  }, [movie.missing_subtitles, movie.subtitles]);

  return <SimpleTable columns={columns} data={data}></SimpleTable>;
};

export default connect(undefined, { update: movieUpdateInfoAll })(Table);
