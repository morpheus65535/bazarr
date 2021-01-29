import React, { FunctionComponent } from "react";
import { connect } from "react-redux";

import { Badge } from "react-bootstrap";
import { AsyncButton } from "../../components";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTrash, faSearch } from "@fortawesome/free-solid-svg-icons";

import { EpisodesApi } from "../../apis";

import { updateSeriesInfo } from "../../@redux/actions";

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
        <span className="pr-1">{subtitle.code2}</span>
        <FontAwesomeIcon
          size="sm"
          icon={missing ? faSearch : faTrash}
        ></FontAwesomeIcon>
      </AsyncButton>
    );
  } else {
    return (
      <Badge className="mr-1" variant="secondary">
        {subtitle.code2}
      </Badge>
    );
  }
};

export const SubtitleAction = connect(undefined, { update: updateSeriesInfo })(
  Action
);
