import { isNumber, isString } from "lodash";
import { ReactText } from "react";

export function isReactText(v: any): v is ReactText {
  return isString(v) || isNumber(v);
}

export function isMovie(v: any): v is Movie {
  return "radarrId" in v;
}

export function isEpisode(v: any): v is Episode {
  return "sonarrEpisodeId" in v;
}

export function isSeries(v: any): v is Series {
  return "episodeFileCount" in v;
}
