import { Dispatch } from "react";

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

export * from "./hooks";
export * from "./validate";
