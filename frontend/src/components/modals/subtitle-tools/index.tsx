import { useSubtitleAction } from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import { SimpleTable } from "@/components/tables";
import { useCustomSelection } from "@/components/tables/plugins";
import { useModals, withModal } from "@/modules/modals";
import { createTask, dispatchTask } from "@/modules/task/utilities";
import { isMovie } from "@/utilities";
import { LOG } from "@/utilities/console";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge, Button, Divider, Group, Menu, Stack } from "@mantine/core";
import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { Column, useRowSelect } from "react-table";
import { tools } from "./tools";

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

export function useProcess(selections: TableColumnType[]) {
  const { mutateAsync } = useSubtitleAction();
  return useCallback(
    (action: string, override?: Partial<FormType.ModifySubtitle>) => {
      LOG("info", "executing action", action);
      const tasks = selections.map((s) => {
        const form: FormType.ModifySubtitle = {
          id: s.id,
          type: s.type,
          language: s.language,
          path: s.path,
          ...override,
        };
        return createTask(s.path, mutateAsync, { action, form });
      });

      dispatchTask(tasks, "modify-subtitles");
    },
    [mutateAsync, selections]
  );
}

interface SubtitleToolViewProps {
  payload: SupportType[];
}

const SubtitleToolView: FunctionComponent<SubtitleToolViewProps> = ({
  payload,
}) => {
  // const Modal = useModal({
  //   size: "lg",
  // });
  // const { show } = useModalControl();

  const [selections, setSelections] = useState<TableColumnType[]>([]);

  const modals = useModals();

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
            return path.slice(idx + 1);
          } else {
            return path;
          }
        },
      },
    ],
    []
  );

  const data = useMemo<TableColumnType[]>(
    () =>
      payload?.flatMap((item) => {
        const [id, type] = getIdAndType(item);
        return item.subtitles.flatMap((v) => {
          if (v.path !== null) {
            return [
              {
                id,
                type,
                language: v.code2,
                path: v.path,
                raw_language: v,
              },
            ];
          } else {
            return [];
          }
        });
      }) ?? [],
    [payload]
  );

  const plugins = [useRowSelect, useCustomSelection];

  const process = useProcess([]);

  return (
    <Stack>
      <SimpleTable
        emptyText="No External Subtitles Found"
        plugins={plugins}
        columns={columns}
        onSelect={setSelections}
        canSelect={CanSelectSubtitle}
        data={data}
      ></SimpleTable>
      <Divider></Divider>
      <Group>
        <Menu
          withArrow
          placement="center"
          control={
            <Button disabled={selections.length === 0} variant="light">
              Select Action
            </Button>
          }
        >
          {tools.map((tool) => (
            <Menu.Item
              key={tool.key}
              icon={<FontAwesomeIcon icon={tool.icon}></FontAwesomeIcon>}
              onClick={() => {
                if (tool.modal) {
                  modals.openContextModal(tool.modal, {});
                } else {
                  process(tool.key);
                }
              }}
            >
              {tool.name}
            </Menu.Item>
          ))}
        </Menu>
      </Group>
    </Stack>
  );
};

export const SubtitleToolModal = withModal(SubtitleToolView, "subtitle-tools");
