import React, { FunctionComponent, useMemo } from "react";
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
  profile?: LanguagesProfile;
  update: (id: number) => void;
}

const Action: FunctionComponent<Props> = ({
  seriesid,
  episodeid,
  missing,
  subtitle,
  profile,
  update,
}) => {
  // hi, forced
  const [hi, forced] = useMemo(() => {
    const item = profile?.items.find((v) => v.language === subtitle.code2);

    if (item) {
      return [item.hi === "True", item.forced === "True"];
    } else {
      return [false, false];
    }
  }, [profile?.items, subtitle.code2]);

  const path = subtitle.path;

  if (missing) {
    return (
      <AsyncButton
        promise={() =>
          EpisodesApi.downloadSubtitles(seriesid, episodeid, {
            hi,
            forced,
            language: subtitle.code2,
          })
        }
        onSuccess={() => update(seriesid)}
        as={Badge}
        className="mr-1"
        variant="warning"
      >
        {subtitle.code2}
        <FontAwesomeIcon
          className="ml-1"
          size="sm"
          icon={faSearch}
        ></FontAwesomeIcon>
      </AsyncButton>
    );
  } else if (path) {
    return (
      <AsyncButton
        promise={() =>
          EpisodesApi.deleteSubtitles(seriesid, episodeid, {
            hi,
            forced,
            path,
            language: subtitle.code2,
          })
        }
        onSuccess={() => update(seriesid)}
        as={Badge}
        className="mr-1"
        variant="secondary"
      >
        {subtitle.code2}
        <FontAwesomeIcon
          className="ml-1"
          size="sm"
          icon={faTrash}
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
