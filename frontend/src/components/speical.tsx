import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { EpisodesApi, MoviesApi } from "../apis";
import { AsyncButton } from "./buttons";

export const SeriesBlacklistButton: FunctionComponent<{
  seriesid: number;
  episodeid: number;
  subs_id?: string;
  language?: Language;
  provider?: string;
  subtitles_path: string;
  path: string;
  update: () => void;
}> = ({
  seriesid,
  episodeid,
  subs_id,
  language,
  provider,
  subtitles_path,
  path,
  update,
}) => {
  if (!language) {
    return null;
  }
  const { hi, forced, code2 } = language;

  if (subs_id && provider && hi !== undefined && forced !== undefined) {
    return (
      <AsyncButton
        size="sm"
        variant="light"
        promise={() =>
          EpisodesApi.addBlacklist(seriesid, episodeid, {
            provider,
            subs_id,
            subtitles_path,
            path: path,
            language: code2,
            hi,
            forced,
          })
        }
        onSuccess={update}
      >
        <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
      </AsyncButton>
    );
  } else {
    return null;
  }
};

export const MoviesBlacklistButton: FunctionComponent<{
  radarrId: number;
  subs_id?: string;
  language?: Language;
  provider?: string;
  subtitles_path: string;
  path: string;
  update: () => void;
}> = ({
  radarrId,
  subs_id,
  language,
  provider,
  subtitles_path,
  path,
  update,
}) => {
  if (!language) {
    return null;
  }

  const { forced, code2 } = language;

  if (subs_id && provider && forced !== undefined) {
    return (
      <AsyncButton
        size="sm"
        variant="light"
        promise={() =>
          MoviesApi.addBlacklist(radarrId, {
            provider,
            subs_id,
            path: path,
            subtitles_path,
            language: code2,
            hi: false,
            forced,
          })
        }
        onSuccess={update}
      >
        <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
      </AsyncButton>
    );
  } else {
    return null;
  }
};
