import { Dispatch } from "react";
import { isEpisode, isMovie, isNullable, isSeries } from "./validate";

export function updateAsyncState<T>(
  promise: Promise<T>,
  setter: (state: AsyncState<T>) => void,
  defaultVal: T
) {
  setter({
    updating: true,
    data: defaultVal,
  });
  promise
    .then((data) => {
      setter({
        updating: false,
        data: data,
      });
    })
    .catch((err) => {
      setter({
        updating: false,
        error: err,
        data: defaultVal,
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

export function buildOrderList<T>(state: OrderIdState<T>): T[] {
  const { items, order } = state;
  return order.flatMap((v) => {
    if (v !== null && v in items) {
      const item = items[v];
      return [item];
    }

    return [];
  });
}

// Replace elements in old array with news
export function mergeArray<T>(
  olds: readonly T[],
  news: readonly T[],
  comparer: Comparer<NonNullable<T>>
) {
  const list = [...olds];
  const newList = news.filter((v) => !isNullable(v)) as NonNullable<T>[];
  // Performance
  newList.forEach((v) => {
    const idx = list.findIndex((n, idx) => {
      if (!isNullable(n)) {
        return comparer(n, v);
      } else {
        return false;
      }
    });
    if (idx !== -1) {
      list[idx] = v;
    } else {
      list.push(v);
    }
  });
  return list;
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

export * from "./hooks";
export * from "./validate";
