import { FunctionComponent } from "react";
import {
  Alert,
  em,
  Flex,
  Group,
  List,
  Popover,
  Stack,
  Text,
} from "@mantine/core";
import { useDisclosure, useMediaQuery } from "@mantine/hooks";
import {
  faCheckCircle,
  faExclamationCircle,
  faListCheck,
  faMinus,
  faPlus,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { BuildKey } from "@/utilities";

interface StateIconProps {
  matches: string[];
  dont: string[];
  isHistory: boolean;
}

const StateIcon: FunctionComponent<StateIconProps> = ({
  matches,
  dont,
  isHistory,
}) => {
  const hasIssues = dont.length > 0;

  const [opened, { close, open }] = useDisclosure(false);

  const isMobile = useMediaQuery(`(max-width: ${em(750)})`);

  const itemSize = isMobile ? "sm" : "md";

  const titleSize = isMobile ? "md" : "lg";

  const popoverTarget = isHistory ? (
    <FontAwesomeIcon icon={faListCheck} />
  ) : (
    <Text size={itemSize} c={hasIssues ? "warning" : "success"} span>
      <FontAwesomeIcon icon={hasIssues ? faExclamationCircle : faCheckCircle} />
    </Text>
  );

  return (
    <Popover
      position={isMobile ? "top" : "left"}
      opened={opened}
      width={360}
      withArrow
      withinPortal
    >
      <Popover.Target>
        <Text
          onMouseEnter={open}
          onMouseLeave={close}
          onClick={opened ? close : open}
        >
          {popoverTarget}
        </Text>
      </Popover.Target>
      <Popover.Dropdown>
        <Text size={titleSize} fw="bold" ta="center">
          Scoring Criteria
        </Text>
        <Group justify="left" gap="xl" wrap="nowrap" grow>
          <Stack align="flex-start" justify="flex-start" gap="xs" mb="auto">
            <Flex gap="sm">
              <Text size={itemSize} c="success">
                <FontAwesomeIcon icon={faPlus}></FontAwesomeIcon>
              </Text>
              <Text size={itemSize} c="success">
                Matching
              </Text>
            </Flex>
            <List size={itemSize} c="success">
              {matches.map((v, idx) => (
                <List.Item key={BuildKey(idx, v, "match")}>{v}</List.Item>
              ))}
            </List>
          </Stack>
          <Stack align="flex-start" justify="flex-start" gap="xs" mb="auto">
            <Flex gap="sm">
              <Text size={itemSize} c="warning">
                <FontAwesomeIcon icon={faMinus}></FontAwesomeIcon>
              </Text>
              <Text size={itemSize} c="warning">
                Not Matching
              </Text>
            </Flex>
            <List size={itemSize} c="warning">
              {dont.map((v, idx) => (
                <List.Item key={BuildKey(idx, v, "miss")}>{v}</List.Item>
              ))}
            </List>
          </Stack>
        </Group>
        <Alert variant="light" color="info" mb="sm">
          <Text size={itemSize}>
            These criteria are used to determine relative rankings. They will
            not prevent automatic downloading of a subtitle unless the score
            falls below your set threshold.
          </Text>
        </Alert>
      </Popover.Dropdown>
    </Popover>
  );
};

export default StateIcon;
