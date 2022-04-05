import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Card as MantineCard,
  Center,
  Divider,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { FunctionComponent } from "react";

interface GroupProps {
  header: string;
  hidden?: boolean;
}

export const Group: FunctionComponent<GroupProps> = ({
  header,
  hidden,
  children,
}) => {
  return (
    <Stack hidden={hidden}>
      <Title order={4}>{header}</Title>
      <Divider></Divider>
      {children}
    </Stack>
  );
};

export interface InputProps {
  name?: string;
  hidden?: boolean;
}

export const Input: FunctionComponent<InputProps> = ({
  children,
  name,
  hidden,
}) => {
  return (
    <Stack hidden={hidden}>
      {name && <Text>{name}</Text>}
      {children}
    </Stack>
  );
};

interface CardProps {
  header?: string;
  subheader?: string;
  plus?: boolean;
  onClick?: () => void;
}

// TODO: Change to button
export const Card: FunctionComponent<CardProps> = ({
  header,
  subheader,
  plus,
  onClick,
}) => {
  return (
    <MantineCard
      style={{ width: "100%", minHeight: "5.6rem" }}
      p="lg"
      shadow="sm"
      onClick={() => onClick && onClick()}
    >
      {plus ? (
        <Center style={{ height: "100%" }}>
          <FontAwesomeIcon size="2x" icon={faPlus}></FontAwesomeIcon>
        </Center>
      ) : (
        <>
          <MantineCard.Section>
            <Text>{header}</Text>
          </MantineCard.Section>
          <MantineCard.Section hidden={subheader === undefined}>
            <Text>{subheader}</Text>
          </MantineCard.Section>
        </>
      )}
    </MantineCard>
  );
};
