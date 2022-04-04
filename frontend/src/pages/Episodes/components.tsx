import { useEpisodeSubtitleModification } from "@/apis/hooks";
import { AsyncButton } from "@/components/async";
import Language from "@/components/bazarr/Language";
import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Badge } from "@mantine/core";
import { FunctionComponent } from "react";

interface Props {
  seriesId: number;
  episodeId: number;
  missing?: boolean;
  subtitle: Subtitle;
}

export const SubtitleAction: FunctionComponent<Props> = ({
  seriesId,
  episodeId,
  missing,
  subtitle,
}) => {
  const { hi, forced } = subtitle;

  const path = subtitle.path;

  const { download, remove } = useEpisodeSubtitleModification();

  if (missing || path) {
    return (
      <AsyncButton
        promise={() => {
          if (missing) {
            return download.mutateAsync({
              seriesId,
              episodeId,
              form: {
                hi,
                forced,
                language: subtitle.code2,
              },
            });
          } else if (path) {
            return remove.mutateAsync({
              seriesId,
              episodeId,
              form: { hi, forced, path, language: subtitle.code2 },
            });
          } else {
            return null;
          }
        }}
        // color={missing ? "primary" : "secondary"}
      >
        <Language.Text className="pr-1" value={subtitle}></Language.Text>
        <FontAwesomeIcon
          size="sm"
          icon={missing ? faSearch : faTrash}
        ></FontAwesomeIcon>
      </AsyncButton>
    );
  } else {
    return (
      <Badge className="mr-1" color="secondary">
        <Language.Text value={subtitle} long={false}></Language.Text>
      </Badge>
    );
  }
};
