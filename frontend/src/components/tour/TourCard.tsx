import { FunctionComponent, RefObject } from "react";
import {
  Alert,
  Button,
  CloseButton,
  Divider,
  Group,
  Progress,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import {
  faArrowLeft,
  faArrowRight,
  faCircleCheck,
  faTriangleExclamation,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { TourStep } from "./types";
import styles from "./Tour.module.scss";

interface TourCardProps {
  step: TourStep;
  stepNumber: number;
  totalSteps: number;
  isBlocked: boolean;
  isFirstStep: boolean;
  isLastStep: boolean;
  hasAction: boolean;
  cardRef: RefObject<HTMLDivElement | null>;
  bodyRef: RefObject<HTMLDivElement | null>;
  onFinish: () => void;
  onNext: () => void;
  onPrevious: () => void;
}

const TourCard: FunctionComponent<TourCardProps> = ({
  step,
  stepNumber,
  totalSteps,
  isBlocked,
  isFirstStep,
  isLastStep,
  hasAction,
  cardRef,
  bodyRef,
  onFinish,
  onNext,
  onPrevious,
}) => {
  return (
    <div ref={cardRef} tabIndex={-1} className={styles.card}>
      <div ref={bodyRef} className={styles.cardBody}>
        <Stack gap="sm">
          <Group
            justify="space-between"
            wrap="nowrap"
            align="flex-start"
            gap="xs"
          >
            <Group
              gap="xs"
              wrap="nowrap"
              align="flex-start"
              style={{ minWidth: 0 }}
            >
              {step.icon !== undefined && (
                <ThemeIcon variant="light" size="lg" radius="md">
                  <FontAwesomeIcon icon={step.icon}></FontAwesomeIcon>
                </ThemeIcon>
              )}
              <div style={{ minWidth: 0 }}>
                <Text size="xs" c="dimmed" fw={600} tt="uppercase">
                  Step {stepNumber} of {totalSteps}
                </Text>
                <Title order={4} data-testid="onboarding-tour-title">
                  {step.title}
                </Title>
              </div>
            </Group>
            <CloseButton
              aria-label="Close tour"
              onClick={onFinish}
            ></CloseButton>
          </Group>
          <Progress
            value={(stepNumber / totalSteps) * 100}
            size="sm"
            radius="xl"
            aria-label="Tour progress"
          ></Progress>
          {isBlocked && step.blockedMessage !== undefined && (
            <Alert
              color="warning"
              variant="light"
              icon={<FontAwesomeIcon icon={faTriangleExclamation} />}
            >
              {step.blockedMessage}
            </Alert>
          )}
          <Text size="sm" c="dimmed" component="div">
            {step.description}
          </Text>
          {step.action !== undefined && (
            <div className={styles.action}>{step.action}</div>
          )}
        </Stack>
      </div>
      <div className={styles.cardFooter}>
        <Divider />
        <Group justify="space-between" mt="sm">
          <Button
            variant="transparent"
            color="gray"
            size="xs"
            styles={{ root: { paddingInline: 0 } }}
            onClick={onFinish}
          >
            Skip tour
          </Button>
          <Group gap="xs">
            <Button
              variant="default"
              size="xs"
              disabled={isFirstStep}
              onClick={onPrevious}
              leftSection={<FontAwesomeIcon icon={faArrowLeft} />}
            >
              Back
            </Button>
            {step.optional === true && (
              <Button
                size="xs"
                variant="light"
                disabled={isBlocked}
                onClick={onNext}
                rightSection={<FontAwesomeIcon icon={faArrowRight} />}
              >
                Skip this step
              </Button>
            )}
            {!hasAction && (
              <Button
                size="xs"
                disabled={isBlocked}
                onClick={onNext}
                rightSection={
                  <FontAwesomeIcon
                    icon={isLastStep ? faCircleCheck : faArrowRight}
                  />
                }
              >
                {isLastStep ? "Finish" : "Next"}
              </Button>
            )}
          </Group>
        </Group>
      </div>
    </div>
  );
};

export default TourCard;
