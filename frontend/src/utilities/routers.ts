// Navigation blocker utility using React Router's useBlocker with Mantine confirmation modal

import { useEffect, useRef } from "react";
import { useBlocker } from "react-router";
import { modals } from "@mantine/modals";

export function usePrompt(when: boolean, message: string) {
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      when && currentLocation.pathname !== nextLocation.pathname,
  );

  const prevWhen = useRef(when);

  useEffect(() => {
    if (blocker.state === "blocked" && prevWhen.current === when) {
      modals.openConfirmModal({
        title: "Unsaved Changes",
        children: message,
        labels: { confirm: "Leave", cancel: "Stay" },
        confirmProps: { color: "red" },
        onConfirm: () => blocker.proceed(),
        onCancel: () => blocker.reset(),
        closeOnCancel: true,
        closeOnConfirm: true,
      });
    }
    prevWhen.current = when;
  }, [blocker, message, when]);
}
