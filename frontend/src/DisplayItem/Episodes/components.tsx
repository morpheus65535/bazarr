import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { Badge } from "react-bootstrap";
import api from "src/apis/raw";
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
            return api.episodes.downloadSubtitles(seriesid, episodeid, {
              hi,
              forced,
              language: subtitle.code2,
            });
          } else if (path) {
            return api.episodes.deleteSubtitles(seriesid, episodeid, {
              hi,
              forced,
              path: path,
              language: subtitle.code2,
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
