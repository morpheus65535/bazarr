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
import Language from "@/components/bazarr/Language";
import SubtitleToolsMenu from "@/components/SubtitleToolsMenu";
import SimpleTable from "@/components/tables/SimpleTable";
import { withModal } from "@/modules/modals";
import { isMovie } from "@/utilities";

type SupportType = Item.Episode | Item.Movie;

type TableColumnType = FormType.ModifySubtitle & {
  raw_language: Language.Info;
};

function getIdAndType(item: SupportType): [number, "episode" | "movie"] {
  if (isMovie(item)) {
    return [item.radarrId, "movie"];
  } else {
    return [item.sonarrEpisodeId, "episode"];
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
        const [id, type] = getIdAndType(item);
        return item.subtitles.flatMap((v) => {
          if (v.path) {
            return [
              {
                id,
                type,
                language: v.code2 ?? "",
                path: v.path,
                // eslint-disable-next-line camelcase
                raw_language: v,
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
        <SubtitleToolsMenu selections={selections}>
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
