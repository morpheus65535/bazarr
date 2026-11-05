import { RefObject, useCallback, useLayoutEffect, useRef } from "react";

export interface ReorderAnimation {
  containerRef: RefObject<HTMLDivElement | null>;
  /** Capture element positions before a reorder; call right before mutating order. */
  capture: () => void;
}

const requirementIdAttribute = "data-requirement-id";
const animationDurationMs = 200;

const findRequirementElements = (container: HTMLElement): HTMLElement[] =>
  Array.from(
    container.querySelectorAll<HTMLElement>(`[${requirementIdAttribute}]`),
  );

// FLIP animation for reordering a keyed list: capture positions before the
// reorder, then translate each moved element back and let it slide into place.
export const useReorderAnimation = (orderKey: string): ReorderAnimation => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const positionsRef = useRef<Map<string, DOMRect>>(new Map());

  const capture = useCallback(() => {
    const container = containerRef.current;
    const capturedPositions = new Map<string, DOMRect>();

    if (container) {
      for (const element of findRequirementElements(container)) {
        const id = element.dataset.requirementId;

        if (id) {
          capturedPositions.set(id, element.getBoundingClientRect());
        }
      }
    }

    positionsRef.current = capturedPositions;
  }, []);

  useLayoutEffect(() => {
    const previousPositions = positionsRef.current;
    positionsRef.current = new Map();

    const container = containerRef.current;

    if (
      previousPositions.size === 0 ||
      container === null ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }

    const animatedElements: HTMLElement[] = [];

    for (const element of findRequirementElements(container)) {
      const id = element.dataset.requirementId;
      const firstRect = id ? previousPositions.get(id) : undefined;

      if (!firstRect) {
        continue;
      }

      const offsetY = firstRect.top - element.getBoundingClientRect().top;

      if (offsetY === 0) {
        continue;
      }

      element.style.transition = "none";
      element.style.transform = `translateY(${offsetY}px)`;
      animatedElements.push(element);
    }

    if (animatedElements.length === 0) {
      return;
    }

    const frame = requestAnimationFrame(() => {
      for (const element of animatedElements) {
        element.style.transition = `transform ${animationDurationMs}ms ease`;
        element.style.transform = "";

        const clearTransitionStyles = () => {
          element.style.transition = "";
          element.removeEventListener("transitionend", clearTransitionStyles);
        };

        element.addEventListener("transitionend", clearTransitionStyles);
      }
    });

    return () => cancelAnimationFrame(frame);
  }, [orderKey]);

  return { containerRef, capture };
};
