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

  const PopoverTarget: FunctionComponent = () => {
    if (isHistory) {
      return <FontAwesomeIcon icon={faListCheck} />;
    } else {
      return (
        <Text c={hasIssues ? "yellow" : "green"} span>
          <FontAwesomeIcon
            icon={hasIssues ? faExclamationCircle : faCheckCircle}
          />
        </Text>
      );
    }
  };

  return (
    <Popover position="left" opened={opened} width={360} withArrow withinPortal>
      <Popover.Target>
        <Text onMouseEnter={open} onMouseLeave={close}>
          <PopoverTarget />
        </Text>
      </Popover.Target>
      <Popover.Dropdown>
        <Text size="xl" ta="center">
          Scoring Criteria
        </Text>
        {isMobile ? null : (
          <Alert variant="light" color="blue" mb="sm">
            Not matching attributes will not prevent the subtitle to be
            downloaded and are strictly used for scoring the subtitle.
          </Alert>
        )}
        <Group justify="left" gap="xl" wrap="nowrap" grow>
          <Stack align="flex-start" justify="flex-start" gap="xs" mb="auto">
            <Flex gap="sm">
              <Text c="green">
                <FontAwesomeIcon icon={faPlus}></FontAwesomeIcon>
              </Text>
              <Text c="green">Matching</Text>
            </Flex>
            <List>
              {matches.map((v, idx) => (
                <List.Item key={BuildKey(idx, v, "match")}>{v}</List.Item>
              ))}
            </List>
          </Stack>
          <Stack align="flex-start" justify="flex-start" gap="xs" mb="auto">
            <Flex gap="sm">
              <Text c="yellow">
                <FontAwesomeIcon icon={faMinus}></FontAwesomeIcon>
              </Text>
              <Text c="yellow">Not Matching</Text>
            </Flex>
            <List>
              {dont.map((v, idx) => (
                <List.Item key={BuildKey(idx, v, "miss")}>{v}</List.Item>
              ))}
            </List>
          </Stack>
        </Group>
      </Popover.Dropdown>
    </Popover>
  );
};

export default StateIcon;
