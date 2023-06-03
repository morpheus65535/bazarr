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
import React, { FunctionComponent } from "react";

const StateIcon: FunctionComponent<{
  matches: string[];
  dont: string[];
  hasIssues: boolean;
  isHistory: boolean;
}> = ({ matches, dont, hasIssues, isHistory }) => {
  const { ref, hovered } = useHover();

  interface PopoverTargetProps {
    ref: React.MutableRefObject<HTMLDivElement>;
    hasIssues: boolean;
    isHistory: boolean;
  }

  function PopoverTarget({ ...props }: PopoverTargetProps) {
    if (isHistory) {
      return (
        <Text ref={ref}>
          <FontAwesomeIcon icon={faListCheck}></FontAwesomeIcon>
        </Text>
      );
    }
    return (
      <Text color={hasIssues ? "yellow" : "green"} ref={ref}>
        <FontAwesomeIcon
          icon={hasIssues ? faExclamationCircle : faCheckCircle}
        ></FontAwesomeIcon>
      </Text>
    );
  }

  return (
    <Popover opened={hovered} position="top" width={360} withArrow>
      <Popover.Target>
        <PopoverTarget ref={ref} hasIssues={hasIssues} isHistory={isHistory} />
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
