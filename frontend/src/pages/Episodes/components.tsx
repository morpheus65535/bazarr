import { useEpisodeSubtitleModification } from "@/apis/hooks";
import { AsyncButton } from "@/components";
import Language from "@/components/bazarr/Language";
import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { Badge } from "react-bootstrap";

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
        as={Badge}
        className="mr-1"
        variant={missing ? "primary" : "secondary"}
      >
        <Language className="pr-1" text={subtitle}></Language>
        <FontAwesomeIcon
          size="sm"
          icon={missing ? faSearch : faTrash}
        ></FontAwesomeIcon>
      </AsyncButton>
    );
  } else {
    return (
      <Badge className="mr-1" variant="secondary">
        <Language value={subtitle} long={false}></Language>
      </Badge>
    );
  }
};
