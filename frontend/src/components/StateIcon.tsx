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

  const PopoverTarget: FunctionComponent = () => {
    if (isHistory) {
      return <FontAwesomeIcon icon={faListCheck} />;
    } else {
      return (
        <Text size={itemSize} c={hasIssues ? "yellow" : "green"} span>
          <FontAwesomeIcon
            icon={hasIssues ? faExclamationCircle : faCheckCircle}
          />
        </Text>
      );
    }
  };

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
          <PopoverTarget />
        </Text>
      </Popover.Target>
      <Popover.Dropdown>
        <Text size={titleSize} fw="bold" c="white" ta="center">
          Scoring Criteria
        </Text>
        <Group justify="left" gap="xl" wrap="nowrap" grow>
          <Stack align="flex-start" justify="flex-start" gap="xs" mb="auto">
            <Flex gap="sm">
              <Text size={itemSize} c="green">
                <FontAwesomeIcon icon={faPlus}></FontAwesomeIcon>
              </Text>
              <Text size={itemSize} c="green">
                Matching
              </Text>
            </Flex>
            <List size={itemSize} c="green">
              {matches.map((v, idx) => (
                <List.Item key={BuildKey(idx, v, "match")}>{v}</List.Item>
              ))}
            </List>
          </Stack>
          <Stack align="flex-start" justify="flex-start" gap="xs" mb="auto">
            <Flex gap="sm">
              <Text size={itemSize} c="yellow">
                <FontAwesomeIcon icon={faMinus}></FontAwesomeIcon>
              </Text>
              <Text size={itemSize} c="yellow">
                Not Matching
              </Text>
            </Flex>
            <List size={itemSize} c="yellow">
              {dont.map((v, idx) => (
                <List.Item key={BuildKey(idx, v, "miss")}>{v}</List.Item>
              ))}
            </List>
          </Stack>
        </Group>
        <Alert variant="light" color="blue" mb="sm">
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
