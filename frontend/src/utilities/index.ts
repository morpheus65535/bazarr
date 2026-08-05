import { Dispatch } from "react";
import { difference, differenceWith } from "lodash";
import { isEpisode, isMovie, isSeries } from "./validate";

export const toggleState = (
  dispatch: Dispatch<boolean>,
  wait: number,
  start = false,
) => {
  dispatch(!start);
  setTimeout(() => dispatch(start), wait);
};

export const GetItemId = <T extends object>(item: T): number | undefined => {
  if (isMovie(item)) {
    return item.radarrId;
  } else if (isEpisode(item)) {
    return item.sonarrEpisodeId;
  } else if (isSeries(item)) {
    return item.sonarrSeriesId;
  } else {
    return undefined;
  }
};

export const BuildKey = (...args: unknown[]) => args.join("-");

export const Reload = () => {
  window.location.reload();
};

export const ScrollToTop = () => {
  window.scrollTo(0, 0);
};

const pathReplaceReg = new RegExp("/{1,}", "g");
export const pathJoin = (...parts: string[]) => {
  const separator = "/";
  return parts.join(separator).replace(pathReplaceReg, separator);
};

export const filterSubtitleBy = (
  subtitles: Subtitle[],
  languages: Language.Info[],
): Subtitle[] => {
  if (languages.length === 0) {
    return subtitles.filter((subtitle) => {
      return subtitle.path !== null;
    });
  } else {
    const result = differenceWith(
      subtitles,
      languages,
      (a, b) => a.code2 === b.code2 || a.path !== null || a.code2 === undefined,
    );
    return difference(subtitles, result);
  }
};

export const fromPython = (value: PythonBoolean | undefined): boolean =>
  value === "True";

export const toPython = (value: boolean): PythonBoolean =>
  value ? "True" : "False";

export * from "./env";
export * from "./hooks";
export * from "./case";
export * from "./validate";
