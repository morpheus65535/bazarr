import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent, useMemo } from "react";
import { Badge } from "react-bootstrap";
import { Column } from "react-table";
import { useMovieSubtitleModification } from "src/apis/hooks";
import { useProfileItemsToLanguages } from "src/utilities/languages";
import { useShowOnlyDesired } from "../../@redux/hooks";
import { AsyncButton, LanguageText, SimpleTable } from "../../components";
import { filterSubtitleBy } from "../../utilities";

const missingText = "Missing Subtitles";

interface Props {
  movie: Item.Movie;
  disabled?: boolean;
  profile?: Language.Profile;
}

const Table: FunctionComponent<Props> = ({ movie, profile, disabled }) => {
  const onlyDesired = useShowOnlyDesired();

  const profileItems = useProfileItemsToLanguages(profile);

  const columns: Column<Subtitle>[] = useMemo<Column<Subtitle>[]>(
    () => [
      {
        Header: "Subtitle Path",
        accessor: "path",
        Cell: ({ value }) => {
          if (value === null || value.length === 0) {
            return "Video File Subtitle Track";
          } else if (value === missingText) {
            return <span className="text-muted">{value}</span>;
          } else {
            return value;
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
          const {
            original: { code2, hi, forced, path },
          } = row.row;

          const { download, remove } = useMovieSubtitleModification();
          const { radarrId } = movie;

          if (path === null || path.length === 0) {
            return null;
          } else if (path === missingText) {
            return (
              <AsyncButton
                disabled={disabled}
                promise={() =>
                  download.mutateAsync({
                    radarrId,
                    form: {
                      language: code2,
                      hi,
                      forced,
                    },
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
                disabled={disabled}
                variant="light"
                size="sm"
                promise={() =>
                  remove.mutateAsync({
                    radarrId,
                    form: {
                      language: code2,
                      hi,
                      forced,
                      path,
                    },
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
    [movie, disabled]
  );

  const data: Subtitle[] = useMemo(() => {
    const missing = movie.missing_subtitles.map((item) => ({
      ...item,
      path: missingText,
    }));

    let raw_subtitles = movie.subtitles;
    if (onlyDesired) {
      raw_subtitles = filterSubtitleBy(raw_subtitles, profileItems);
    }

    return [...raw_subtitles, ...missing];
  }, [movie.missing_subtitles, movie.subtitles, onlyDesired, profileItems]);

  return (
    <SimpleTable
      columns={columns}
      data={data}
      emptyText="No Subtitles Found For This Movie"
    ></SimpleTable>
  );
};

export default Table;
