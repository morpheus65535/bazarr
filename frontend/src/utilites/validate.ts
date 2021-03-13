import { isNull, isNumber, isString, isUndefined } from "lodash";
import { ReactText } from "react";

export function isReactText(v: any): v is ReactText {
  return isString(v) || isNumber(v);
}

export function isNonNullable<T>(v: T): v is NonNullable<T> {
  return !isNull(v) && !isUndefined(v);
}

export function isMovie(v: any): v is Item.Movie {
  return "radarrId" in v;
}

export function isEpisode(v: any): v is Item.Episode {
  return "sonarrEpisodeId" in v;
}

export function isSeries(v: any): v is Item.Series {
  return "episodeFileCount" in v;
}
