import { faSearch, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { Badge } from "react-bootstrap";
import { connect } from "react-redux";
import { seriesUpdateInfoAll } from "../../@redux/actions";
import { EpisodesApi } from "../../apis";
import { AsyncButton, SubtitleText } from "../../components";

interface Props {
  seriesid: number;
  episodeid: number;
  missing?: boolean;
  subtitle: Subtitle;
  update: (id: number) => void;
}

const Action: FunctionComponent<Props> = ({
  seriesid,
  episodeid,
  missing,
  subtitle,
  update,
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
          }
        }}
        onSuccess={() => update(seriesid)}
        as={Badge}
        className="mr-1"
        variant={missing ? "warning" : "secondary"}
      >
        <SubtitleText className="pr-1" subtitle={subtitle}></SubtitleText>
        <FontAwesomeIcon
          size="sm"
          icon={missing ? faSearch : faTrash}
        ></FontAwesomeIcon>
      </AsyncButton>
    );
  } else {
    return (
      <Badge className="mr-1" variant="secondary">
        <SubtitleText subtitle={subtitle}></SubtitleText>
      </Badge>
    );
  }
};

export const SubtitleAction = connect(undefined, {
  update: seriesUpdateInfoAll,
})(Action);
