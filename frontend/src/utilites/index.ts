import { ReactText } from "react";
import { isString, isNumber } from "lodash";

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

export function isReactText(v: any): v is ReactText {
  return isString(v) || isNumber(v);
}

export * from "./hooks";
