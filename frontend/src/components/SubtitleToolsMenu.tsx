import { useSubtitleAction } from "@/apis/hooks";
import { ColorToolModal } from "@/components/forms/ColorToolForm";
import { FrameRateModal } from "@/components/forms/FrameRateForm";
import { TimeOffsetModal } from "@/components/forms/TimeOffsetForm";
import { TranslationModal } from "@/components/forms/TranslationForm";
import { useModals } from "@/modules/modals";
import { ModalComponent } from "@/modules/modals/WithModal";
import { createTask, dispatchTask } from "@/modules/task";
import {
  faClock,
  faCode,
  faDeaf,
  faExchangeAlt,
  faFilm,
  faImage,
  faLanguage,
  faMagic,
  faPaintBrush,
  faPlay,
  faSearch,
  faTextHeight,
  faTrash,
  IconDefinition,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Divider, List, Menu, MenuProps, ScrollArea } from "@mantine/core";
import { FunctionComponent, ReactElement, useCallback, useMemo } from "react";

export interface ToolOptions {
  key: string;
  icon: IconDefinition;
  name: string;
  modal?: ModalComponent<{
    selections: FormType.ModifySubtitle[];
  }>;
}

export function useTools() {
  return useMemo<ToolOptions[]>(
    () => [
      {
        key: "sync",
        icon: faPlay,
        name: "Sync",
      },
      {
        key: "remove_HI",
        icon: faDeaf,
        name: "Remove HI Tags",
      },
      {
        key: "remove_tags",
        icon: faCode,
        name: "Remove Style Tags",
      },
      {
        key: "OCR_fixes",
        icon: faImage,
        name: "OCR Fixes",
      },
      {
        key: "common",
        icon: faMagic,
        name: "Common Fixes",
      },
      {
        key: "fix_uppercase",
        icon: faTextHeight,
        name: "Fix Uppercase",
      },
      {
        key: "reverse_rtl",
        icon: faExchangeAlt,
        name: "Reverse RTL",
      },
      {
        key: "add_color",
        icon: faPaintBrush,
        name: "Add Color...",
        modal: ColorToolModal,
      },
      {
        key: "change_frame_rate",
        icon: faFilm,
        name: "Change Frame Rate...",
        modal: FrameRateModal,
      },
      {
        key: "adjust_time",
        icon: faClock,
        name: "Adjust Times...",
        modal: TimeOffsetModal,
      },
      {
        key: "translation",
        icon: faLanguage,
        name: "Translate...",
        modal: TranslationModal,
      },
    ],
    []
  );
}

interface Props {
  selections: FormType.ModifySubtitle[];
  children?: ReactElement;
  menu?: Omit<MenuProps, "control" | "children">;
  onAction?: (action: "delete" | "search") => void;
}

const SubtitleToolsMenu: FunctionComponent<Props> = ({
  selections,
  children,
  menu,
  onAction,
}) => {
  const { mutateAsync } = useSubtitleAction();

  const process = useCallback(
    (action: string, name: string) => {
      const tasks = selections.map((s) => {
        const form: FormType.ModifySubtitle = {
          id: s.id,
          type: s.type,
          language: s.language,
          path: s.path,
        };
        return createTask(s.path, mutateAsync, { action, form });
      });

      dispatchTask(tasks, name);
    },
    [mutateAsync, selections]
  );

  const tools = useTools();
  const modals = useModals();

  const disabledTools = selections.length === 0;

  return (
    <Menu control={children} {...menu}>
      <Menu.Label>Tools</Menu.Label>
      {tools.map((tool) => (
        <Menu.Item
          key={tool.key}
          disabled={disabledTools}
          icon={<FontAwesomeIcon icon={tool.icon}></FontAwesomeIcon>}
          onClick={() => {
            if (tool.modal) {
              modals.openContextModal(tool.modal, { selections });
            } else {
              process(tool.key, tool.name);
            }
          }}
        >
          {tool.name}
        </Menu.Item>
      ))}
      <Divider></Divider>
      <Menu.Label>Actions</Menu.Label>
      <Menu.Item
        disabled={selections.length !== 0 || onAction === undefined}
        icon={<FontAwesomeIcon icon={faSearch}></FontAwesomeIcon>}
        onClick={() => {
          onAction?.("search");
        }}
      >
        Search
      </Menu.Item>
      <Menu.Item
        disabled={selections.length === 0 || onAction === undefined}
        color="red"
        icon={<FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>}
        onClick={() => {
          modals.openConfirmModal({
            title: "The following subtitles will be deleted",
            size: "lg",
            children: (
              <ScrollArea style={{ maxHeight: "20rem" }}>
                <List>
                  {selections.map((s) => (
                    <List.Item my="md" key={s.path}>
                      {s.path}
                    </List.Item>
                  ))}
                </List>
              </ScrollArea>
            ),
            onConfirm: () => {
              onAction?.("delete");
            },
            labels: { confirm: "Delete", cancel: "Cancel" },
            confirmProps: { color: "red" },
          });
        }}
      >
        Delete...
      </Menu.Item>
    </Menu>
  );
};

export default SubtitleToolsMenu;
