import {
  FunctionComponent,
  PropsWithChildren,
  ReactNode,
  useId,
  useState,
} from "react";
import {
  Divider,
  Group,
  Stack,
  Text,
  Title,
  UnstyledButton,
} from "@mantine/core";
import {
  faChevronDown,
  faChevronRight,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

interface SectionProps {
  header: string;
  hidden?: boolean;
  /** When true, the header becomes a clickable toggle with a chevron. */
  collapsible?: boolean;
  /** Initial open state when collapsible (defaults to open). */
  defaultCollapsed?: boolean;
  /** Inline helper text rendered next to the header. */
  summary?: ReactNode;
}

type Props = PropsWithChildren<SectionProps>;

export const Section: FunctionComponent<Props> = ({
  header,
  hidden,
  collapsible,
  defaultCollapsed,
  summary,
  children,
}) => {
  const [open, setOpen] = useState<boolean>(!collapsible || !defaultCollapsed);
  const contentId = useId();

  const headerContent = (
    <Group gap="xs" wrap="nowrap" align="center">
      <Title order={4}>{header}</Title>
      {summary && (
        <Text c="dimmed" size="sm" component="span">
          {summary}
        </Text>
      )}
    </Group>
  );

  return (
    <Stack
      display={hidden ? "none" : undefined}
      gap="xs"
      my="lg"
      data-testid={`section-${header}`}
    >
      {collapsible ? (
        <UnstyledButton
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls={contentId}
          data-testid={`section-toggle-${header}`}
          style={{ width: "100%", textAlign: "left" }}
        >
          <Group justify="space-between" gap="xs" wrap="nowrap">
            {headerContent}
            <FontAwesomeIcon
              icon={open ? faChevronDown : faChevronRight}
              size="xs"
            />
          </Group>
        </UnstyledButton>
      ) : (
        headerContent
      )}
      <Divider></Divider>
      <Stack
        id={contentId}
        gap="xs"
        display={open ? undefined : "none"}
        data-testid={`section-content-${header}`}
      >
        {children}
      </Stack>
    </Stack>
  );
};
