import { useEpisodeSubtitleModification } from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import SubtitleToolsMenu from "@/components/SubtitleToolsMenu";
import { createAndDispatchTask } from "@/modules/task";
import { Badge, DefaultMantineColor } from "@mantine/core";
import { FunctionComponent, useMemo } from "react";

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
  const color: DefaultMantineColor | undefined = useMemo(() => {
    if (missing) {
      return "yellow";
    } else if (subtitle.path === null) {
      return "gray";
    }
  }, [missing, subtitle.path]);

  const selections = useMemo<FormType.ModifySubtitle[]>(() => {
    const list: FormType.ModifySubtitle[] = [];

    if (subtitle.path !== null) {
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
        opened: subtitle.path === null ? false : undefined,
      }}
      selections={selections}
      onAction={(action) => {
        if (action === "search") {
          createAndDispatchTask(
            subtitle.name,
            "Searching subtitle...",
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
        } else if (action === "delete" && subtitle.path !== null) {
          createAndDispatchTask(
            subtitle.name,
            "Deleting subtitle...",
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
      <Badge color={color}>
        <Language.Text value={subtitle} long={false}></Language.Text>
      </Badge>
    </SubtitleToolsMenu>
  );
};
