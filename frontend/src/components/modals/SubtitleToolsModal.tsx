import Language from "@/components/bazarr/Language";
import SubtitleToolsMenu from "@/components/SubtitleToolsMenu";
import { SimpleTable } from "@/components/tables";
import { useCustomSelection } from "@/components/tables/plugins";
import { withModal } from "@/modules/modals";
import { isMovie } from "@/utilities";
import { Badge, Button, Divider, Group, Stack, Text } from "@mantine/core";
import { FunctionComponent, useMemo, useState } from "react";
import { Column, useRowSelect } from "react-table";

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

  const columns: Column<TableColumnType>[] = useMemo<Column<TableColumnType>[]>(
    () => [
      {
        Header: "Language",
        accessor: "raw_language",
        Cell: ({ value }) => (
          <Badge color="secondary">
            <Language.Text value={value} long></Language.Text>
          </Badge>
        ),
      },
      {
        id: "file",
        Header: "File",
        accessor: "path",
        Cell: ({ value }) => {
          const path = value;

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
    []
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
                language: v.code2,
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
    [payload]
  );

  const plugins = [useRowSelect, useCustomSelection];

  return (
    <Stack>
      <SimpleTable
        tableStyles={{ emptyText: "No external subtitles found" }}
        plugins={plugins}
        columns={columns}
        onSelect={setSelections}
        canSelect={CanSelectSubtitle}
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
