import { FunctionComponent, ReactElement, useCallback, useMemo } from "react";
import { Divider, List, Menu, MenuProps, ScrollArea } from "@mantine/core";
import {
  faBoxOpen,
  faSearch,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useSubtitleAction } from "@/apis/hooks";
import { useModals } from "@/modules/modals";
import { task } from "@/modules/task";
import { useTools } from "./useTools";
import styles from "./SubtitleToolsMenu.module.scss";

interface Props {
  selections: FormType.ModifySubtitle[];
  children?: ReactElement;
  menu?: Omit<MenuProps, "children">;
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
      selections.forEach((s) => {
        const description = s.path ?? s.mediaTitle ?? "Unknown subtitle";
        task.create(description, name, mutateAsync, { action, form: s });
      });
    },
    [mutateAsync, selections],
  );

  const tools = useTools();
  const modals = useModals();

  const isExternalOnly = useMemo(
    () => selections.length > 0 && selections.every((s) => s.path !== null),
    [selections],
  );
  const isSingleEmbedded = useMemo(
    () => selections.length === 1 && selections[0].path === null,
    [selections],
  );

  // Embedded subtitles only support a few actions, so show a stripped-down menu
  // that omits (rather than disables) the unsupported tools and actions. This
  // avoids confusion such as "why can't I delete my embedded subtitles?".
  // Translating an embedded track extracts it first (server-side) and is only
  // offered for a single selection, mirroring the Extract action.
  const translationTool = tools.find((t) => t.key === "translation");
  const showTools = isExternalOnly;
  const showSearch = selections.length === 0;
  const showExtract = isSingleEmbedded;
  const showEmbeddedTranslate = isSingleEmbedded;
  const showDelete = isExternalOnly;

  return (
    <Menu withArrow withinPortal position="left-end" {...menu}>
      <Menu.Target>{children}</Menu.Target>
      <Menu.Dropdown>
        {showTools && (
          <>
            <Menu.Label>Tools</Menu.Label>
            {tools.map((tool) => (
              <Menu.Item
                key={tool.key}
                leftSection={
                  <FontAwesomeIcon icon={tool.icon}></FontAwesomeIcon>
                }
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
          </>
        )}
        {showEmbeddedTranslate && translationTool?.modal && (
          <>
            <Menu.Label>Tools</Menu.Label>
            <Menu.Item
              leftSection={
                <FontAwesomeIcon icon={translationTool.icon}></FontAwesomeIcon>
              }
              onClick={() => {
                modals.openContextModal(translationTool.modal!, { selections });
              }}
            >
              {translationTool.name}
            </Menu.Item>
            <Divider></Divider>
          </>
        )}
        {(showSearch || showExtract || showDelete) && (
          <Menu.Label>Actions</Menu.Label>
        )}
        {showSearch && (
          <Menu.Item
            disabled={onAction === undefined}
            leftSection={<FontAwesomeIcon icon={faSearch}></FontAwesomeIcon>}
            onClick={() => {
              onAction?.("search");
            }}
          >
            Search
          </Menu.Item>
        )}
        {showExtract && (
          <Menu.Item
            leftSection={<FontAwesomeIcon icon={faBoxOpen}></FontAwesomeIcon>}
            onClick={() => {
              process("extract", "Extract");
            }}
          >
            Extract
          </Menu.Item>
        )}
        {showDelete && (
          <Menu.Item
            disabled={onAction === undefined}
            color="danger"
            className={styles.deleteItem}
            leftSection={<FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>}
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
                confirmProps: { color: "danger" },
              });
            }}
          >
            Delete...
          </Menu.Item>
        )}
      </Menu.Dropdown>
    </Menu>
  );
};

export default SubtitleToolsMenu;
