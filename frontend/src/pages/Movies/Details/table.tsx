import { useMovieSubtitleModification } from "@/apis/hooks";
import { useShowOnlyDesired } from "@/apis/hooks/site";
import { Action, SimpleTable } from "@/components";
import Language from "@/components/bazarr/Language";
import SubtitleToolsMenu from "@/components/SubtitleToolsMenu";
import { task, TaskGroup } from "@/modules/task";
import { useTableStyles } from "@/styles";
import { filterSubtitleBy } from "@/utilities";
import { useProfileItemsToLanguages } from "@/utilities/languages";
import { faEllipsis, faSearch } from "@fortawesome/free-solid-svg-icons";
import { Badge, Text, TextProps } from "@mantine/core";
import { isString } from "lodash";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";

const missingText = "Missing Subtitles";

interface Props {
  movie: Item.Movie | null;
  disabled?: boolean;
  profile?: Language.Profile;
}

function isSubtitleTrack(path: string | undefined | null) {
  return !isString(path) || path.length === 0;
}

function isSubtitleMissing(path: string | undefined | null) {
  return path === missingText;
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
          const { classes } = useTableStyles();

          const props: TextProps<"div"> = {
            className: classes.primary,
          };

          if (isSubtitleTrack(value)) {
            return <Text {...props}>Video File Subtitle Track</Text>;
          } else if (isSubtitleMissing(value)) {
            return (
              <Text {...props} color="dimmed">
                {value}
              </Text>
            );
          } else {
            return <Text {...props}>{value}</Text>;
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
        Cell: ({ row }) => {
          const {
            original: { code2, path, hi, forced },
          } = row;

          const { download, remove } = useMovieSubtitleModification();

          const selections = useMemo(() => {
            const list: FormType.ModifySubtitle[] = [];

            if (path && !isSubtitleMissing(path) && movie !== null) {
              list.push({
                type: "movie",
                path,
                id: movie.radarrId,
                language: code2,
              });
            }

            return list;
          }, [code2, path]);

          if (movie === null) {
            return null;
          }

          const { radarrId } = movie;

          if (isSubtitleMissing(path)) {
            return (
              <Action
                label="Search Subtitle"
                icon={faSearch}
                disabled={disabled}
                onClick={() => {
                  task.create(
                    movie.title,
                    TaskGroup.SearchSubtitle,
                    download.mutateAsync,
                    {
                      radarrId,
                      form: {
                        language: code2,
                        forced,
                        hi,
                      },
                    }
                  );
                }}
              ></Action>
            );
          }

          return (
            <SubtitleToolsMenu
              selections={selections}
              onAction={(action) => {
                if (action === "delete" && path) {
                  task.create(
                    movie.title,
                    TaskGroup.DeleteSubtitle,
                    remove.mutateAsync,
                    {
                      radarrId,
                      form: {
                        language: code2,
                        forced,
                        hi,
                        path,
                      },
                    }
                  );
                } else if (action === "search") {
                  throw new Error(
                    "This shouldn't happen, please report the bug"
                  );
                }
              }}
            >
              <Action
                label="Subtitle Actions"
                disabled={isSubtitleTrack(path)}
                icon={faEllipsis}
              ></Action>
            </SubtitleToolsMenu>
          );
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
      tableStyles={{ emptyText: "No subtitles found for this movie" }}
    ></SimpleTable>
  );
};

export default Table;
