import { useEffect, useState } from "react";
import { getScrollAdjustment, getUnionRect, isSameRectSet } from "./geometry";
import { ResolvedRects, ResolvedSpotlight, TourRect } from "./types";

const targetTimeoutMs = 4000;
const targetPollIntervalMs = 50;
const headerClearancePx = 8;

const noGroups: HTMLElement[][] = [];
const noElements: HTMLElement[] = [];

const collectElements = (selector: string): HTMLElement[] =>
  Array.from(document.querySelectorAll<HTMLElement>(selector));

const getHeaderHeight = (): number => {
  const header = document.querySelector<HTMLElement>(
    ".mantine-AppShell-header",
  );
  return header?.getBoundingClientRect().height ?? 0;
};

// Keeps every target clear of the fixed header and the bottom edge; without
// this a top target like Save can end up highlighted behind the top bar.
const keepTargetsVisible = (elements: HTMLElement[]): void => {
  const union = getUnionRect(elements);
  if (union === null) {
    return;
  }

  const adjustment = getScrollAdjustment({
    top: union.top,
    bottom: union.top + union.height,
    availableTop: getHeaderHeight() + headerClearancePx,
    availableBottom: window.innerHeight - headerClearancePx,
  });

  if (adjustment === 0) {
    return;
  }
  window.scrollBy?.(0, adjustment);
};

const getUnionRects = (groups: HTMLElement[][]): TourRect[] =>
  groups
    .map((group) => getUnionRect(group))
    .filter((rect): rect is TourRect => rect !== null);

interface SpotlightParams {
  isOpened: boolean;
  stepIndex: number;
  pathname: string;
  /** The step's route: targets are only resolved once the route matches. */
  route?: string;
  targets: string[];
}

export const useTourSpotlight = ({
  isOpened,
  stepIndex,
  pathname,
  route,
  targets,
}: SpotlightParams) => {
  const [spotlight, setSpotlight] = useState<ResolvedSpotlight | null>(null);
  const [resolvedRects, setResolvedRects] = useState<ResolvedRects | null>(
    null,
  );

  useEffect(() => {
    if (!isOpened) {
      return;
    }
    if (route !== undefined && pathname !== route) {
      return;
    }
    if (targets.length === 0) {
      return;
    }

    const runState = { isCancelled: false };
    const startedAt = Date.now();

    const poll = () => {
      if (runState.isCancelled) {
        return;
      }
      const primaryGroup = collectElements(targets[0]);
      if (primaryGroup.length > 0) {
        // Resolve as soon as the anchor target exists; extra targets are
        // spotlighted when present (e.g. the checkbox column in table view).
        const groups = targets.map(collectElements);
        keepTargetsVisible(groups.flat());
        setSpotlight({ stepIndex, groups });
        return;
      }
      if (Date.now() - startedAt < targetTimeoutMs) {
        window.setTimeout(poll, targetPollIntervalMs);
      }
    };

    const firstPoll = window.setTimeout(poll, 0);

    return () => {
      runState.isCancelled = true;
      window.clearTimeout(firstPoll);
    };
  }, [isOpened, stepIndex, pathname, route, targets]);

  const groups =
    spotlight !== null && spotlight.stepIndex === stepIndex
      ? spotlight.groups
      : noGroups;

  // A per-frame loop (state only when the rects change) catches layout shifts
  // that scroll/resize events miss, e.g. the bulk bar re-rendering.
  useEffect(() => {
    if (groups.length === 0) {
      return;
    }

    const frameState = { handle: 0 };
    const tick = () => {
      const rects = getUnionRects(groups);
      setResolvedRects((previous) => {
        const isUnchanged =
          previous !== null &&
          previous.stepIndex === stepIndex &&
          isSameRectSet(previous.rects, rects);
        if (isUnchanged) {
          return previous;
        }
        return { stepIndex, rects };
      });
      frameState.handle = window.requestAnimationFrame(tick);
    };

    frameState.handle = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frameState.handle);
  }, [groups, stepIndex]);

  return { primaryElements: groups[0] ?? noElements, resolvedRects };
};
