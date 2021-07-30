import { Async } from "../types/async";

export namespace AsyncUtility {
  export function getDefaultItem<T>(): Async.Item<T> {
    return {
      state: "idle",
      content: null,
      error: null,
    };
  }
}
