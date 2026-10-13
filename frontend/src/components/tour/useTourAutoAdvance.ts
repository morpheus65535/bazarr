import { useEffect } from "react";
import { TourStep } from "./types";

interface AutoAdvanceParams {
  isOpened: boolean;
  step: TourStep;
  primaryElements: HTMLElement[];
  onAdvance: () => void;
}

const actionAdvanceDelayMs = 300;
const saveAdvanceDelayMs = 100;
const presentPollIntervalMs = 300;

/**
 * Advances each step when its action completes, so no Next button is needed.
 */
export const useTourAutoAdvance = ({
  isOpened,
  step,
  primaryElements,
  onAdvance,
}: AutoAdvanceParams): void => {
  useEffect(() => {
    if (!isOpened || step.isFulfilled !== true) {
      return;
    }
    const handle = window.setTimeout(onAdvance, 0);
    return () => window.clearTimeout(handle);
  }, [isOpened, onAdvance, step.isFulfilled]);

  // Media toolbar controls (Select / Select all / Save) are plain buttons, so
  // a click means the action is complete.
  useEffect(() => {
    if (!isOpened || step.advanceOnAction !== "primary") {
      return;
    }
    if (primaryElements.length === 0) {
      return;
    }
    const onClick = () => {
      window.setTimeout(onAdvance, actionAdvanceDelayMs);
    };
    primaryElements.forEach((element) =>
      element.addEventListener("click", onClick),
    );
    return () =>
      primaryElements.forEach((element) =>
        element.removeEventListener("click", onClick),
      );
  }, [isOpened, primaryElements, onAdvance, step.advanceOnAction]);

  // The Settings Save button: wait for the backend to confirm the save rather
  // than advancing on the click.
  useEffect(() => {
    if (!isOpened || step.advanceOnAction !== "secondary") {
      return;
    }
    const onSaved = () => {
      window.setTimeout(onAdvance, saveAdvanceDelayMs);
    };
    window.addEventListener("bazarr-settings-saved", onSaved);
    return () => window.removeEventListener("bazarr-settings-saved", onSaved);
  }, [isOpened, onAdvance, step.advanceOnAction]);

  // Some controls open a dropdown, so advance once a marker element rendered by
  // the app appears (e.g. after a profile has been staged).
  useEffect(() => {
    if (!isOpened || step.advanceWhenPresent === undefined) {
      return;
    }
    const selector = step.advanceWhenPresent;
    const state = { handle: 0 };
    const check = () => {
      if (document.querySelector(selector) !== null) {
        onAdvance();
        return;
      }
      state.handle = window.setTimeout(check, presentPollIntervalMs);
    };
    state.handle = window.setTimeout(check, 0);
    return () => window.clearTimeout(state.handle);
  }, [isOpened, onAdvance, step.advanceWhenPresent]);

  // Idle fallback for optional settings left unchanged.
  useEffect(() => {
    if (!isOpened || step.autoAdvanceMs === undefined) {
      return;
    }
    const state = { handle: 0 };
    const schedule = () => {
      window.clearTimeout(state.handle);
      state.handle = window.setTimeout(onAdvance, step.autoAdvanceMs);
    };
    schedule();
    window.addEventListener("mousedown", schedule);
    window.addEventListener("keydown", schedule);
    return () => {
      window.clearTimeout(state.handle);
      window.removeEventListener("mousedown", schedule);
      window.removeEventListener("keydown", schedule);
    };
  }, [isOpened, onAdvance, step.autoAdvanceMs]);
};
