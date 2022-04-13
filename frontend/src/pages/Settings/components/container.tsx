import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Center,
  createStyles,
  Divider,
  Stack,
  Text,
  Title,
  UnstyledButton,
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
    <Stack hidden={hidden} spacing="xs">
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
    <Stack hidden={hidden} spacing="xs" mb="md">
      {name && <Text>{name}</Text>}
      {children}
    </Stack>
  );
};

const useCardStyles = createStyles((theme) => {
  return {
    card: {
      borderRadius: theme.radius.sm,
      border: `1px solid ${theme.colors.gray[7]}`,

      "&:hover": {
        boxShadow: theme.shadows.md,
        border: `1px solid ${theme.colors.brand[5]}`,
      },
    },
    stack: {
      height: "100%",
    },
  };
});

interface CardProps {
  header?: string;
  description?: string;
  plus?: boolean;
  onClick?: () => void;
}

// TODO: Change to button
export const Card: FunctionComponent<CardProps> = ({
  header,
  description,
  plus,
  onClick,
}) => {
  const { classes } = useCardStyles();
  return (
    <UnstyledButton p="lg" onClick={onClick} className={classes.card}>
      {plus ? (
        <Center>
          <FontAwesomeIcon size="2x" icon={faPlus}></FontAwesomeIcon>
        </Center>
      ) : (
        <Stack className={classes.stack} spacing={0} align="flex-start">
          <Text weight="bold">{header}</Text>
          <Text hidden={description === undefined}>{description}</Text>
        </Stack>
      )}
    </UnstyledButton>
  );
};
