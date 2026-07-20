import { FunctionComponent, useMemo, useState } from "react";
import { Badge, MantineColor } from "@mantine/core";
import { useEpisodeSubtitleModification } from "@/apis/hooks";
import Language from "@/components/bazarr/Language";
import SubtitleToolsMenu from "@/components/SubtitleToolsMenu";
import { toPython } from "@/utilities";

interface Props {
  seriesId: number;
  episodeId: number;
  mediaTitle?: string;
  missing?: boolean;
  subtitle: Subtitle;
}

export const Subtitle: FunctionComponent<Props> = ({
  seriesId,
  episodeId,
  mediaTitle,
  missing = false,
  subtitle,
}) => {
  const { remove, download } = useEpisodeSubtitleModification();

  const [opened, setOpen] = useState(false);

  const isEmbedded = subtitle.path === null;

  const variant: MantineColor | undefined = useMemo(() => {
    if (opened && !isEmbedded) {
      return "highlight";
    } else if (missing) {
      return "warning";
    } else if (isEmbedded) {
      return "disabled";
    }
  }, [isEmbedded, missing, opened]);

  const selections = useMemo<FormType.ModifySubtitle[]>(() => {
    const list: FormType.ModifySubtitle[] = [];

    if (!missing) {
      list.push({
        id: episodeId,
        subtitlesId: subtitle.id,
        type: "episode",
        language: subtitle.code2,
        path: subtitle.path ?? null,
        mediaTitle,
        forced: toPython(subtitle.forced),
        hi: toPython(subtitle.hi),
      });
    }

    return list;
  }, [
    episodeId,
    missing,
    subtitle.id,
    subtitle.code2,
    subtitle.path,
    subtitle.forced,
    subtitle.hi,
    mediaTitle,
  ]);

  return (
    <SubtitleToolsMenu
      menu={{
        trigger: "hover",
        onOpen: () => setOpen(true),
        onClose: () => setOpen(false),
      }}
      selections={selections}
      onAction={async (action) => {
        if (action === "search") {
          await download.mutateAsync({
            seriesId,
            episodeId,
            form: {
              language: subtitle.code2,
              hi: subtitle.hi,
              forced: subtitle.forced,
            },
          });
        } else if (action === "delete" && subtitle.path) {
          await remove.mutateAsync({
            seriesId,
            episodeId,
            form: {
              language: subtitle.code2,
              hi: subtitle.hi,
              forced: subtitle.forced,
              path: subtitle.path,
            },
          });
        }
      }}
    >
      <Badge variant={variant}>
        <Language.Text value={subtitle} long={false}></Language.Text>
      </Badge>
    </SubtitleToolsMenu>
  );
};
