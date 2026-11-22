import { FunctionComponent, ReactNode, useId } from "react";
import { createPortal } from "react-dom";
import { Paper, Popover } from "@mantine/core";
import { TourPlacement, TourRect } from "./types";
import styles from "./Tour.module.scss";

interface TourOverlayProps {
  isTargeted: boolean;
  isInteractive: boolean;
  placement: TourPlacement;
  anchorRect: TourRect;
  highlightRects: TourRect[];
  hasResolvedRects: boolean;
  children: ReactNode;
}

const popoverZIndex = 150;
const highlightRadius = 8;

const TourOverlay: FunctionComponent<TourOverlayProps> = ({
  isTargeted,
  isInteractive,
  placement,
  anchorRect,
  highlightRects,
  hasResolvedRects,
  children,
}) => {
  const maskId = `tour-mask-${useId().replace(/:/g, "")}`;

  if (!isTargeted) {
    return createPortal(
      <div
        className={styles.centeredWrapper}
        data-testid="onboarding-backdrop"
        style={{
          pointerEvents: isInteractive ? "none" : undefined,
          background: isInteractive ? "transparent" : undefined,
        }}
      >
        <Paper
          shadow="xl"
          radius="md"
          p="lg"
          className={styles.centeredCard}
          style={{ pointerEvents: "auto" }}
        >
          {children}
        </Paper>
      </div>,
      document.body,
    );
  }

  const dimColor = isInteractive ? "rgba(0, 0, 0, 0.4)" : "rgba(0, 0, 0, 0.62)";

  return createPortal(
    <>
      <div
        className={styles.backdrop}
        data-testid="onboarding-backdrop"
        style={{ pointerEvents: isInteractive ? "none" : undefined }}
      />
      <svg
        className={styles.overlay}
        data-testid="onboarding-highlight"
        aria-hidden="true"
      >
        <defs>
          <mask
            id={maskId}
            maskUnits="userSpaceOnUse"
            x="0"
            y="0"
            width="100%"
            height="100%"
          >
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            {highlightRects.map((rect, index) => (
              <rect
                key={index}
                x={rect.left}
                y={rect.top}
                width={rect.width}
                height={rect.height}
                rx={highlightRadius}
                fill="black"
              />
            ))}
          </mask>
        </defs>
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill={dimColor}
          mask={`url(#${maskId})`}
        />
        {hasResolvedRects &&
          highlightRects.map((rect, index) => (
            <rect
              key={index}
              x={rect.left}
              y={rect.top}
              width={rect.width}
              height={rect.height}
              rx={highlightRadius}
              fill="none"
              stroke="var(--mantine-color-brand-5)"
              strokeWidth={2}
            />
          ))}
      </svg>
      <Popover
        opened
        position={placement}
        offset={16}
        withArrow
        withinPortal
        shadow="xl"
        radius="md"
        width="min(440px, calc(100vw - 32px))"
        middlewares={{ flip: false, shift: true, inline: false }}
        zIndex={popoverZIndex}
        closeOnClickOutside={false}
        closeOnEscape={false}
      >
        <Popover.Target>
          <div
            className={styles.anchor}
            style={{
              top: anchorRect.top,
              left: anchorRect.left,
              width: anchorRect.width,
              height: anchorRect.height,
            }}
          />
        </Popover.Target>
        <Popover.Dropdown p="lg">{children}</Popover.Dropdown>
      </Popover>
    </>,
    document.body,
  );
};

export default TourOverlay;
