import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { Badge } from "react-bootstrap";
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
          } else {
            return null;
          }
        }}
        className="me-1"
        variant={missing ? "primary" : "secondary"}
      >
        <LanguageText className="pe-1" text={subtitle}></LanguageText>
        <FontAwesomeIcon
          size="sm"
          icon={missing ? faSearch : faTrash}
        ></FontAwesomeIcon>
      </AsyncButton>
    );
  } else {
    return (
      <Badge className="me-1" bg="secondary">
        <LanguageText text={subtitle} long={false}></LanguageText>
      </Badge>
    );
  }
};
