import { isNumber, isString } from "lodash";
import { Dispatch, ReactText } from "react";

export function updateAsyncState<T>(
  promise: Promise<T>,
  setter: (state: AsyncState<T>) => void,
  defaultVal: T
) {
  setter({
    updating: true,
    items: defaultVal,
  });
  promise
    .then((data) => {
      setter({
        updating: false,
        items: data,
      });
    })
    .catch((err) => {
      setter({
        updating: false,
        error: err,
        items: defaultVal,
      });
    });
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
export * from "./hooks";
