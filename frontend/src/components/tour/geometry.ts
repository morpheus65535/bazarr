import { TourRect } from "./types";

export const isSameRectSet = (left: TourRect[], right: TourRect[]): boolean =>
  left.length === right.length &&
  left.every(
    (rect, index) =>
      rect.top === right[index].top &&
      rect.left === right[index].left &&
      rect.width === right[index].width &&
      rect.height === right[index].height,
  );

export const inflateRect = (rect: TourRect, padding: number): TourRect => ({
  top: rect.top - padding,
  left: rect.left - padding,
  width: rect.width + padding * 2,
  height: rect.height + padding * 2,
});

// Collapses every matched element into one rect, so a selector that matches a
// whole column (e.g. the row checkboxes) highlights the column as a unit.
export const getUnionRect = (elements: HTMLElement[]): TourRect | null => {
  const bounds = elements.map((element) => element.getBoundingClientRect());
  if (bounds.length === 0) {
    return null;
  }

  const top = Math.min(...bounds.map((rect) => rect.top));
  const left = Math.min(...bounds.map((rect) => rect.left));
  const right = Math.max(...bounds.map((rect) => rect.right));
  const bottom = Math.max(...bounds.map((rect) => rect.bottom));

  return { top, left, width: right - left, height: bottom - top };
};

interface ScrollAdjustmentParams {
  top: number;
  bottom: number;
  availableTop: number;
  availableBottom: number;
}

export const getScrollAdjustment = ({
  top,
  bottom,
  availableTop,
  availableBottom,
}: ScrollAdjustmentParams): number => {
  if (top < availableTop) {
    return top - availableTop;
  }
  if (bottom > availableBottom) {
    return bottom - availableBottom;
  }
  return 0;
};
