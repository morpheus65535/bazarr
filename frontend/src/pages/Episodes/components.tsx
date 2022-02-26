import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useEpisodeSubtitleModification } from "apis/hooks";
import { AsyncButton, LanguageText } from "components";
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
        <LanguageText className="pr-1" text={subtitle}></LanguageText>
        <FontAwesomeIcon
          size="sm"
          icon={missing ? faSearch : faTrash}
        ></FontAwesomeIcon>
      </AsyncButton>
    );
  } else {
    return (
      <Badge className="mr-1" variant="secondary">
        <LanguageText text={subtitle} long={false}></LanguageText>
      </Badge>
    );
  }
};
