import {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useLocation, useNavigate } from "react-router";
import { useWindowEvent } from "@mantine/hooks";
import { inflateRect } from "./geometry";
import TourCard from "./TourCard";
import TourOverlay from "./TourOverlay";
import { TourProps, TourRect } from "./types";
import { useTourAutoAdvance } from "./useTourAutoAdvance";
import { useTourSpotlight } from "./useTourSpotlight";

export type { TourAdvanceAction, TourPlacement, TourStep } from "./types";

const highlightPadding = 8;
const emptyRects: TourRect[] = [];

const Tour: FunctionComponent<TourProps> = ({
  opened,
  steps,
  initialStepIndex = 0,
  onStepChange,
  onFinish,
}) => {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const [stepIndex, setStepIndex] = useState(() =>
    Math.min(Math.max(initialStepIndex, 0), steps.length - 1),
  );
  const cardRef = useRef<HTMLDivElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);

  const step = steps[stepIndex];
  const stepNumber = stepIndex + 1;
  const totalSteps = steps.length;
  const isFirstStep = stepIndex === 0;
  const isLastStep = stepIndex === totalSteps - 1;
  const isBlocked = step.isBlocked === true;
  const isInteractive = step.interactive === true;
  // Steps with a detectable action (or that auto-skip once fulfilled) advance on
  // their own; only purely informational steps need Next.
  const hasAction =
    step.advanceOnAction !== undefined ||
    step.advanceWhenPresent !== undefined ||
    step.isFulfilled !== undefined;

  const targets = useMemo(
    () =>
      step.target === undefined
        ? []
        : [step.target, ...(step.secondaryTargets ?? [])],
    [step.target, step.secondaryTargets],
  );

  const goToNextStep = useCallback(() => {
    if (isBlocked) {
      return;
    }
    if (isLastStep) {
      onFinish();
      return;
    }
    const nextStepIndex = stepIndex + 1;
    setStepIndex(nextStepIndex);
    onStepChange?.(nextStepIndex);
  }, [isBlocked, isLastStep, onFinish, stepIndex, onStepChange]);

  const goToPreviousStep = useCallback(() => {
    const previousStepIndex = stepIndex === 0 ? 0 : stepIndex - 1;
    setStepIndex(previousStepIndex);
    onStepChange?.(previousStepIndex);
  }, [stepIndex, onStepChange]);

  const { primaryElements, resolvedRects } = useTourSpotlight({
    isOpened: opened,
    stepIndex,
    pathname,
    route: step.route,
    targets,
  });

  useTourAutoAdvance({
    isOpened: opened,
    step,
    primaryElements,
    onAdvance: goToNextStep,
  });

  useEffect(() => {
    if (!opened) {
      return;
    }
    if (step.route === undefined || pathname === step.route) {
      return;
    }
    navigate(step.route);
  }, [opened, step.route, pathname, navigate]);

  useEffect(() => {
    if (!opened) {
      return;
    }
    // preventScroll keeps the browser from scrolling the page when the card is
    // focused on a step change; resetting the body avoids inheriting scroll.
    cardRef.current?.focus({ preventScroll: true });
    bodyRef.current?.scrollTo?.({ top: 0 });
  }, [opened, stepIndex]);

  useWindowEvent("keydown", (event) => {
    if (!opened) {
      return;
    }
    // Let form controls (and their portaled dropdowns) own the keyboard.
    const eventTarget = event.target as HTMLElement | null;
    const isEditableField =
      eventTarget !== null &&
      eventTarget.matches("input, textarea, select, [contenteditable='true']");
    if (isEditableField) {
      return;
    }
    const isInsideCard = cardRef.current?.contains(eventTarget) ?? false;
    if (!isInsideCard && eventTarget !== document.body) {
      return;
    }

    if (event.key === "Escape") {
      onFinish();
      return;
    }
    if (event.key === "ArrowRight") {
      goToNextStep();
      return;
    }
    if (event.key === "ArrowLeft") {
      goToPreviousStep();
    }
  });

  if (!opened) {
    return null;
  }

  const displayRects = resolvedRects?.rects ?? emptyRects;
  const hasResolvedRects = displayRects.length > 0;
  const fallbackRect: TourRect = {
    top: window.innerHeight / 2,
    left: window.innerWidth / 2,
    width: 0,
    height: 0,
  };
  const anchorRect = displayRects[0] ?? fallbackRect;
  const highlightRects =
    displayRects.length === 0
      ? [fallbackRect]
      : displayRects.map((rect) => inflateRect(rect, highlightPadding));

  return (
    <TourOverlay
      isTargeted={step.target !== undefined}
      isInteractive={isInteractive}
      placement={step.placement ?? "bottom"}
      anchorRect={anchorRect}
      highlightRects={highlightRects}
      hasResolvedRects={hasResolvedRects}
    >
      <TourCard
        step={step}
        stepNumber={stepNumber}
        totalSteps={totalSteps}
        isBlocked={isBlocked}
        isFirstStep={isFirstStep}
        isLastStep={isLastStep}
        hasAction={hasAction}
        cardRef={cardRef}
        bodyRef={bodyRef}
        onFinish={onFinish}
        onNext={goToNextStep}
        onPrevious={goToPreviousStep}
      />
    </TourOverlay>
  );
};

export default Tour;
