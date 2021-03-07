import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { Badge } from "react-bootstrap";
import { useSeries } from "../../@redux/hooks";
import { EpisodesApi } from "../../apis";
import { AsyncButton, LanguageText } from "../../components";

interface Props {
  seriesid: number;
  episodeid: number;
  missing?: boolean;
  subtitle: Subtitle;
}

export const SubtitleAction: FunctionComponent<Props> = ({
  seriesid,
  episodeid,
  missing,
  subtitle,
}) => {
  const { hi, forced } = subtitle;

  const [, update] = useSeries();

  const path = subtitle.path;

  if (missing || path) {
    return (
      <AsyncButton
        promise={() => {
          if (missing) {
            return EpisodesApi.downloadSubtitles(seriesid, episodeid, {
              hi,
              forced,
              language: subtitle.code2,
            });
          } else if (path) {
            return EpisodesApi.deleteSubtitles(seriesid, episodeid, {
              hi,
              forced,
              path: path,
              language: subtitle.code2,
            });
          }
        }}
        onSuccess={() => update(seriesid)}
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
        <LanguageText text={subtitle}></LanguageText>
      </Badge>
    );
  }
};
