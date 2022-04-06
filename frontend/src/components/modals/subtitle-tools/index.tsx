import { useSubtitleAction } from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import { SimpleTable } from "@/components/tables";
import { useCustomSelection } from "@/components/tables/plugins";
import {
  useModal,
  useModalControl,
  usePayload,
  withModal,
} from "@/modules/modals";
import { createTask, dispatchTask } from "@/modules/task/utilities";
import { isMovie } from "@/utilities";
import { LOG } from "@/utilities/console";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge, Button, Group, Menu } from "@mantine/core";
import { isObject } from "lodash";
import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { Column, useRowSelect } from "react-table";
import {
  ProcessSubtitleContext,
  ProcessSubtitleType,
  useProcess,
} from "./ToolContext";
import { tools } from "./tools";
import { ToolOptions } from "./types";

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

function isElement(value: unknown): value is JSX.Element {
  return isObject(value);
}

interface SubtitleToolViewProps {
  count: number;
  tools: ToolOptions[];
  select: (items: TableColumnType[]) => void;
}

const SubtitleToolView: FunctionComponent<SubtitleToolViewProps> = ({
  tools,
  count,
  select,
}) => {
  const payload = usePayload<SupportType[]>();

  const Modal = useModal({
    size: "lg",
  });
  const { show } = useModalControl();

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

  const process = useProcess();

  const footer = useMemo(() => {
    return (
      <Group>
        <Menu
          withArrow
          placement="center"
          control={
            <Button disabled={count === 0} variant="light">
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
                  show(tool.modal);
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
    );
  }, [count, process, show, tools]);

  return (
    <Modal title="Subtitle Tools" footer={footer}>
      <SimpleTable
        emptyText="No External Subtitles Found"
        plugins={plugins}
        columns={columns}
        onSelect={select}
        canSelect={CanSelectSubtitle}
        data={data}
      ></SimpleTable>
    </Modal>
  );
};

export const SubtitleToolModal = withModal(SubtitleToolView, "subtitle-tools");

const SubtitleTools: FunctionComponent = () => {
  const modals = useMemo(
    () =>
      tools
        .map((t) => t.modal && <t.modal key={t.key}></t.modal>)
        .filter(isElement),
    []
  );

  const { hide } = useModalControl();
  const [selections, setSelections] = useState<TableColumnType[]>([]);
  const { mutateAsync } = useSubtitleAction();

  const process = useCallback<ProcessSubtitleType>(
    (action, override) => {
      LOG("info", "executing action", action);
      hide(SubtitleToolModal.modalKey);
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
    [hide, selections, mutateAsync]
  );

  return (
    <ProcessSubtitleContext.Provider value={process}>
      <SubtitleToolModal
        count={selections.length}
        tools={tools}
        select={setSelections}
      ></SubtitleToolModal>
      {modals}
    </ProcessSubtitleContext.Provider>
  );
};

export default SubtitleTools;
