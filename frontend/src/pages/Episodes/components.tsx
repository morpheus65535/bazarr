import { useEpisodeSubtitleModification } from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import SubtitleToolsMenu from "@/components/SubtitleToolsMenu";
import { task, TaskGroup } from "@/modules/task";
import { Badge, MantineColor, Tooltip } from "@mantine/core";
import { FunctionComponent, useMemo, useState } from "react";

interface Props {
  seriesId: number;
  episodeId: number;
  missing?: boolean;
  subtitle: Subtitle;
}

export const Subtitle: FunctionComponent<Props> = ({
  seriesId,
  episodeId,
  missing = false,
  subtitle,
}) => {
  const { remove, download } = useEpisodeSubtitleModification();

  const [opened, setOpen] = useState(false);

  const disabled = subtitle.path === null;

  const color: MantineColor | undefined = useMemo(() => {
    if (opened && !disabled) {
      return "cyan";
    } else if (missing) {
      return "yellow";
    } else if (disabled) {
      return "gray";
    }
  }, [disabled, missing, opened]);

  const selections = useMemo<FormType.ModifySubtitle[]>(() => {
    const list: FormType.ModifySubtitle[] = [];

    if (subtitle.path) {
      list.push({
        id: episodeId,
        type: "episode",
        language: subtitle.code2,
        path: subtitle.path,
      });
    }

    return list;
  }, [episodeId, subtitle.code2, subtitle.path]);

  return (
    <SubtitleToolsMenu
      menu={{
        trigger: "hover",
        opened: disabled ? false : undefined,
        onOpen: () => setOpen(true),
        onClose: () => setOpen(false),
      }}
      selections={selections}
      onAction={(action) => {
        if (action === "search") {
          task.create(
            subtitle.name,
            TaskGroup.SearchSubtitle,
            download.mutateAsync,
            {
              seriesId,
              episodeId,
              form: {
                language: subtitle.code2,
                hi: subtitle.hi,
                forced: subtitle.forced,
              },
            }
          );
        } else if (action === "delete" && subtitle.path) {
          task.create(
            subtitle.name,
            TaskGroup.DeleteSubtitle,
            remove.mutateAsync,
            {
              seriesId,
              episodeId,
              form: {
                language: subtitle.code2,
                hi: subtitle.hi,
                forced: subtitle.forced,
                path: subtitle.path,
              },
            }
          );
        }
      }}
    >
      <Tooltip.Floating label="Embedded Subtitle" disabled={!disabled}>
        <Badge color={color}>
          <Language.Text value={subtitle} long={false}></Language.Text>
        </Badge>
      </Tooltip.Floating>
    </SubtitleToolsMenu>
  );
};
