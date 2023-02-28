// A workaround of built-in hooks in React-Router v6
// https://gist.github.com/rmorse/426ffcc579922a82749934826fa9f743

import type { Blocker, History, Transition } from "history";
import { useContext, useEffect } from "react";
// eslint-disable-next-line camelcase
import { UNSAFE_NavigationContext } from "react-router-dom";

export function useBlocker(blocker: Blocker, when = true) {
  const navigator = useContext(UNSAFE_NavigationContext).navigator as History;

  useEffect(() => {
    if (!when) return;

    const unblock = navigator.block((tx: Transition) => {
      const autoUnblockingTx = {
        ...tx,
        retry() {
          // Automatically unblock the transition so it can play all the way
          // through before retrying it. TODO: Figure out how to re-enable
          // this block if the transition is cancelled for some reason.
          unblock();
          tx.retry();
        },
      };

      blocker(autoUnblockingTx);
    });

    return unblock;
  }, [navigator, blocker, when]);
}

// TODO: Replace with Mantine's confirmation modal
export function usePrompt(when: boolean, message: string) {
  useBlocker((tx) => {
    if (window.confirm(message)) {
      tx.retry();
    }
  }, when);
}
