import { Dispatch } from "react";
import { isMovie, isNullable, isSeries } from "./validate";

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

export function getExtendItemId(item: Item.Base): number {
  if (isMovie(item)) {
    return item.radarrId;
  } else if (isSeries(item)) {
    return item.sonarrSeriesId;
  } else {
    return -1;
  }
}

// Replace elements in old array with news
// If not exist, the method will find the first null value and replace it
export function mergeArray<T>(
  olds: readonly T[],
  news: readonly T[],
  comparer: Comparer<NonNullable<T>>
) {
  const list = [...olds];
  const newList = news.filter((v) => !isNullable(v)) as NonNullable<T>[];
  // Performance
  let firstNull = -1;
  newList.forEach((v) => {
    const idx = list.findIndex((n, idx) => {
      if (!isNullable(n)) {
        return comparer(n, v);
      } else {
        firstNull = idx;
        return false;
      }
    });
    if (idx !== -1) {
      list[idx] = v;
    } else if (firstNull !== -1) {
      list[firstNull] = v;
    } else {
      list.push(v);
    }
  });
  return list;
}

export function Reload() {
  window.location.reload();
}

export * from "./hooks";
export * from "./validate";
