import { difference, differenceWith } from "lodash";
import { Dispatch } from "react";
import { isEpisode, isMovie, isSeries } from "./validate";

export function getBaseUrl(slash: boolean = false) {
  let url: string = "/";
  if (process.env.NODE_ENV === "production") {
    url = window.Bazarr.baseUrl;
  }

  const endsWithSlash = url.endsWith("/");
  if (slash && !endsWithSlash) {
    return `${url}/`;
  } else if (!slash && endsWithSlash) {
    return url.slice(0, -1);
  }
  return url;
}

export function copyToClipboard(s: string) {
  let field = document.createElement("textarea");
  field.innerText = s;
  document.body.appendChild(field);
  field.select();
  field.setSelectionRange(0, 9999);
  document.execCommand("copy");
  field.remove();
}

export function toggleState(
  dispatch: Dispatch<boolean>,
  wait: number,
  start: boolean = false
) {
  dispatch(!start);
  setTimeout(() => dispatch(start), wait);
}

export function submodProcessColor(s: string) {
  return `color(name=${s})`;
}

export function GetItemId(item: any): number {
  if (isMovie(item)) {
    return item.radarrId;
  } else if (isEpisode(item)) {
    return item.sonarrEpisodeId;
  } else if (isSeries(item)) {
    return item.sonarrSeriesId;
  } else {
    return -1;
  }
}

export function BuildKey(...args: any[]) {
  return args.join("-");
}

export function Reload() {
  window.location.reload();
}

export function ScrollToTop() {
  window.scrollTo(0, 0);
}

export function filterSubtitleBy(
  subtitles: Subtitle[],
  languages: Language.Info[]
): Subtitle[] {
  if (languages.length === 0) {
    return subtitles.filter((subtitle) => {
      return subtitle.path !== null;
    });
  } else {
    const result = differenceWith(
      subtitles,
      languages,
      (a, b) => a.code2 === b.code2 || a.path !== null || a.code2 === undefined
    );
    return difference(subtitles, result);
  }
}

export * from "./async";
export * from "./entity";
export * from "./hooks";
export * from "./validate";
