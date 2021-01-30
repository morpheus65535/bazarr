import { FillfulActionDispatcher } from "../types";
import reduxStore from "./index";

let checklist: FillfulActionDispatcher[] = [];
let checking = false;

reduxStore.subscribe(() => {
  if (!checking) {
    const state = reduxStore.getState();
    const dispatch = reduxStore.dispatch;

    checking = true;
    checklist = checklist.flatMap((fn) => {
      const action = fn(state);
      if (action === undefined) {
        return fn;
      } else {
        dispatch(action);
        return [];
      }
    });
    checking = false;
  }
});

export function addToChecklist(fn: FillfulActionDispatcher) {
  checklist.push(fn);
}
