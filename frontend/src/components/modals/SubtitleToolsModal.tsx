import { FunctionComponent, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Checkbox,
  Divider,
  Group,
  Stack,
  Text,
} from "@mantine/core";
import { ColumnDef } from "@tanstack/react-table";
import {
  useEpisodeSubtitleModification,
  useMovieSubtitleModification,
} from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import SubtitleToolsMenu from "@/components/SubtitleToolsMenu";
import SimpleTable from "@/components/tables/SimpleTable";
import { useModals, withModal } from "@/modules/modals";
import { fromPython, isMovie, toPython } from "@/utilities";

type SupportType = Item.Episode | Item.Movie;

type TableColumnType = FormType.ModifySubtitle & {
  raw_language: Language.Info;
  seriesId: number;
  name: string;
  isMovie: boolean;
};

type LocalisedType = {
  id: number;
  seriesId: number;
  type: "movie" | "episode";
  name: string;
  isMovie: boolean;
};

function getLocalisedValues(item: SupportType): LocalisedType {
  if (isMovie(item)) {
    return {
      seriesId: 0,
      id: item.radarrId,
      type: "movie",
      name: item.title,
      isMovie: true,
    };
  } else {
    return {
      seriesId: item.sonarrSeriesId,
      id: item.sonarrEpisodeId,
      type: "episode",
      name: item.title,
      isMovie: false,
    };
  }
}

const CanSelectSubtitle = (item: TableColumnType) => {
  return item.path.endsWith(".srt");
};

interface SubtitleToolViewProps {
  payload: SupportType[];
}

const SubtitleToolView: FunctionComponent<SubtitleToolViewProps> = ({
  payload,
}) => {
  const [selections, setSelections] = useState<TableColumnType[]>([]);
  const { remove: removeEpisode, download: downloadEpisode } =
    useEpisodeSubtitleModification();
  const { download: downloadMovie, remove: removeMovie } =
    useMovieSubtitleModification();
  const modals = useModals();

  const columns = useMemo<ColumnDef<TableColumnType>[]>(
    () => [
      {
        id: "selection",
        header: ({ table }) => {
          return (
            <Checkbox
              id="table-header-selection"
              indeterminate={table.getIsSomeRowsSelected()}
              checked={table.getIsAllRowsSelected()}
              onChange={table.getToggleAllRowsSelectedHandler()}
            ></Checkbox>
          );
        },
        cell: ({ row: { index, getIsSelected, getToggleSelectedHandler } }) => {
          return (
            <Checkbox
              id={`table-cell-${index}`}
              checked={getIsSelected()}
              onChange={getToggleSelectedHandler()}
              onClick={getToggleSelectedHandler()}
            ></Checkbox>
          );
        },
      },
      {
        header: "Language",
        accessorKey: "raw_language",
        cell: ({
          row: {
            original: { raw_language: rawLanguage },
          },
        }) => (
          <Badge color="secondary">
            <Language.Text value={rawLanguage} long></Language.Text>
          </Badge>
        ),
      },
      {
        id: "file",
        header: "File",
        accessorKey: "path",
        cell: ({
          row: {
            original: { path },
          },
        }) => {
          let idx = path.lastIndexOf("/");

          if (idx === -1) {
            idx = path.lastIndexOf("\\");
          }

          if (idx !== -1) {
            return <Text>{path.slice(idx + 1)}</Text>;
          } else {
            return <Text>{path}</Text>;
          }
        },
      },
    ],
    [],
  );

  const data = useMemo<TableColumnType[]>(
    () =>
      payload.flatMap((item) => {
        const { seriesId, id, type, name, isMovie } = getLocalisedValues(item);
        return item.subtitles.flatMap((v) => {
          if (v.path) {
            return [
              {
                id,
                seriesId,
                type,
                language: v.code2,
                path: v.path,
                // eslint-disable-next-line camelcase
                raw_language: v,
                name,
                hi: toPython(v.forced),
                forced: toPython(v.hi),
                isMovie,
              },
            ];
          } else {
            return [];
          }
        });
      }),
    [payload],
  );

  return (
    <Stack>
      <SimpleTable
        tableStyles={{ emptyText: "No external subtitles found" }}
        enableRowSelection={(row) => CanSelectSubtitle(row.original)}
        onRowSelectionChanged={(rows) =>
          setSelections(rows.map((r) => r.original))
        }
        columns={columns}
        data={data}
      ></SimpleTable>
      <Divider></Divider>
      <Group>
        <SubtitleToolsMenu
          selections={selections}
          onAction={(action) => {
            selections.forEach(async (selection) => {
              const actionPayload = {
                form: {
                  language: selection.language,
                  hi: fromPython(selection.hi),
                  forced: fromPython(selection.forced),
                  path: selection.path,
                },
                radarrId: 0,
                seriesId: 0,
                episodeId: 0,
              };
              if (selection.isMovie) {
                actionPayload.radarrId = selection.id;
              } else {
                actionPayload.seriesId = selection.seriesId;
                actionPayload.episodeId = selection.id;
              }
              const download = selection.isMovie
                ? downloadMovie
                : downloadEpisode;
              const remove = selection.isMovie ? removeMovie : removeEpisode;

              if (action === "search") {
                await download.mutateAsync(actionPayload);
              } else if (action === "delete" && selection.path) {
                await remove.mutateAsync(actionPayload);
              }
            });
            modals.closeAll();
          }}
        >
          <Button disabled={selections.length === 0} variant="light">
            Select Action
          </Button>
        </SubtitleToolsMenu>
      </Group>
    </Stack>
  );
};

export default withModal(SubtitleToolView, "subtitle-tools", {
  title: "Subtitle Tools",
  size: "xl",
});
