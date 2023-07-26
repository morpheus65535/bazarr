import { BuildKey } from "@/utilities";
import {
  faCheck,
  faCheckCircle,
  faExclamationCircle,
  faListCheck,
  faTimes,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Group, List, Popover, Stack, Text } from "@mantine/core";
import { useHover } from "@mantine/hooks";
import { FunctionComponent } from "react";

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

  const { hovered, ref } = useHover();

  const PopoverTarget: FunctionComponent = () => {
    if (isHistory) {
      return <FontAwesomeIcon icon={faListCheck} />;
    } else {
      return (
        <Text color={hasIssues ? "yellow" : "green"}>
          <FontAwesomeIcon
            icon={hasIssues ? faExclamationCircle : faCheckCircle}
          />
        </Text>
      );
    }
  };

  return (
    <Popover opened={hovered} position="top" width={360} withArrow withinPortal>
      <Popover.Target>
        <Text ref={ref}>
          <PopoverTarget />
        </Text>
      </Popover.Target>
      <Popover.Dropdown>
        <Group position="left" spacing="xl" noWrap grow>
          <Stack align="flex-start" justify="flex-start" spacing="xs" mb="auto">
            <Text color="green">
              <FontAwesomeIcon icon={faCheck}></FontAwesomeIcon>
            </Text>
            <List>
              {matches.map((v, idx) => (
                <List.Item key={BuildKey(idx, v, "match")}>{v}</List.Item>
              ))}
            </List>
          </Stack>
          <Stack align="flex-start" justify="flex-start" spacing="xs" mb="auto">
            <Text color="yellow">
              <FontAwesomeIcon icon={faTimes}></FontAwesomeIcon>
            </Text>
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
