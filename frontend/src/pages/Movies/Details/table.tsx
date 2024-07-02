import React, { FunctionComponent, useMemo } from "react";
import { Badge, Text, TextProps } from "@mantine/core";
import { faEllipsis, faSearch } from "@fortawesome/free-solid-svg-icons";
import { ColumnDef } from "@tanstack/react-table";
import { isString } from "lodash";
import { useMovieSubtitleModification } from "@/apis/hooks";
import { useShowOnlyDesired } from "@/apis/hooks/site";
import { Action } from "@/components";
import Language from "@/components/bazarr/Language";
import SubtitleToolsMenu from "@/components/SubtitleToolsMenu";
import NewSimpleTable from "@/components/tables/NewSimpleTable";
import { task, TaskGroup } from "@/modules/task";
import { filterSubtitleBy, toPython } from "@/utilities";
import { useProfileItemsToLanguages } from "@/utilities/languages";

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

  const { download, remove } = useMovieSubtitleModification();

  const CodeCell = React.memo(({ item }: { item: Subtitle }) => {
    const { code2, path, hi, forced } = item;

    const selections = useMemo(() => {
      const list: FormType.ModifySubtitle[] = [];

      if (path && !isSubtitleMissing(path) && movie !== null) {
        list.push({
          type: "movie",
          path,
          id: movie.radarrId,
          language: code2,
          forced: toPython(forced),
          hi: toPython(hi),
        });
      }

      return list;
    }, [code2, path, forced, hi]);

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
              },
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
              },
            );
          } else if (action === "search") {
            throw new Error("This shouldn't happen, please report the bug");
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
  });

  const columns = useMemo<ColumnDef<Subtitle>[]>(
    () => [
      {
        header: "Subtitle Path",
        accessorKey: "path",
        cell: ({
          row: {
            original: { path },
          },
        }) => {
          const props: TextProps = {
            className: "table-primary",
          };

          if (isSubtitleTrack(path)) {
            return (
              <Text className="table-primary">Video File Subtitle Track</Text>
            );
          } else if (isSubtitleMissing(path)) {
            return (
              <Text {...props} c="dimmed">
                {path}
              </Text>
            );
          } else {
            return <Text {...props}>{path}</Text>;
          }
        },
      },
      {
        header: "Language",
        accessorKey: "name",
        cell: ({ row }) => {
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
        id: "code2",
        cell: ({ row: { original } }) => {
          return <CodeCell item={original} />;
        },
      },
    ],
    [CodeCell],
  );

  const data: Subtitle[] = useMemo(() => {
    const missing =
      movie?.missing_subtitles.map((item) => ({
        ...item,
        path: missingText,
      })) ?? [];

    let rawSubtitles = movie?.subtitles ?? [];
    if (onlyDesired) {
      rawSubtitles = filterSubtitleBy(rawSubtitles, profileItems);
    }

    return [...rawSubtitles, ...missing];
  }, [movie, onlyDesired, profileItems]);

  return (
    <NewSimpleTable
      columns={columns}
      data={data}
      tableStyles={{ emptyText: "No subtitles found for this movie" }}
    ></NewSimpleTable>
  );
};

export default Table;
