import { ReactNode } from "react";
import { IconDefinition } from "@fortawesome/free-solid-svg-icons";

export type TourPlacement = "top" | "bottom" | "left" | "right";

export type TourAdvanceAction = "primary" | "secondary";

export interface TourRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

export interface TourStep {
  id: string;
  title: string;
  description: ReactNode;
  /** Optional interactive controls rendered under the description. */
  action?: ReactNode;
  icon?: IconDefinition;
  /** Navigates here before the step is shown. Omit for a centered step. */
  route?: string;
  /** CSS selector of the element the card anchors to. */
  target?: string;
  /** Extra selectors to spotlight (e.g. the page's Save button). */
  secondaryTargets?: string[];
  placement?: TourPlacement;
  /** Lets the user click and configure the page behind the tour. */
  interactive?: boolean;
  /** Blocks moving forward until the condition is cleared. */
  isBlocked?: boolean;
  /** Warning shown while isBlocked is true. */
  blockedMessage?: ReactNode;
  /** Advances to the next step after the targeted control is clicked. */
  advanceOnAction?: TourAdvanceAction;
  /** Advances once an element matching this selector appears. */
  advanceWhenPresent?: string;
  /** Idle fallback: advances after this many ms without user interaction. */
  autoAdvanceMs?: number;
  /** Optional step: offers a button to continue without doing anything. */
  optional?: boolean;
  /** Already fulfilled: the step advances on its own without interaction. */
  isFulfilled?: boolean;
}

export interface TourProps {
  opened: boolean;
  steps: TourStep[];
  initialStepIndex?: number;
  onStepChange?: (stepIndex: number) => void;
  onFinish: () => void;
}

export interface ResolvedSpotlight {
  stepIndex: number;
  groups: HTMLElement[][];
}

export interface ResolvedRects {
  stepIndex: number;
  rects: TourRect[];
}
