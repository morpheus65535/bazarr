import { useMovieSubtitleModification } from "@/apis/hooks";
import { SimpleTable } from "@/components";
import { AsyncButton } from "@/components/async";
import Language from "@/components/bazarr/Language";
import { useShowOnlyDesired } from "@/modules/redux/hooks";
import { filterSubtitleBy } from "@/utilities";
import { useProfileItemsToLanguages } from "@/utilities/languages";
import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge, Text } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";

const missingText = "Missing Subtitles";

interface Props {
  movie: Item.Movie | null;
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
            return <Text color="dimmed">{value}</Text>;
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
              <Badge color="primary">
                <Language.Text value={row.original} long></Language.Text>
              </Badge>
            );
          } else {
            return (
              <Badge color="secondary">
                <Language.Text value={row.original} long></Language.Text>
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

          if (movie === null) {
            return null;
          }

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
              >
                <FontAwesomeIcon icon={faSearch}></FontAwesomeIcon>
              </AsyncButton>
            );
          } else {
            return (
              <AsyncButton
                disabled={disabled}
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
    const missing =
      movie?.missing_subtitles.map((item) => ({
        ...item,
        path: missingText,
      })) ?? [];

    let raw_subtitles = movie?.subtitles ?? [];
    if (onlyDesired) {
      raw_subtitles = filterSubtitleBy(raw_subtitles, profileItems);
    }

    return [...raw_subtitles, ...missing];
  }, [movie, onlyDesired, profileItems]);

  return (
    <SimpleTable
      columns={columns}
      data={data}
      emptyText="No Subtitles Found For This Movie"
    ></SimpleTable>
  );
};

export default Table;
