import { FunctionComponent } from "react";
import { Center, Stack, Text, UnstyledButton } from "@mantine/core";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import styles from "./Card.module.scss";

interface CardProps {
  header?: string;
  description?: string;
  plus?: boolean;
  onClick?: () => void;
}

export const Card: FunctionComponent<CardProps> = ({
  header,
  description,
  plus,
  onClick,
}) => {
  return (
    <UnstyledButton p="lg" onClick={onClick} className={styles.card}>
      {plus ? (
        <Center>
          <FontAwesomeIcon size="2x" icon={faPlus}></FontAwesomeIcon>
        </Center>
      ) : (
        <Stack h="100%" gap={0} align="flex-start">
          <Text fw="bold">{header}</Text>
          <Text hidden={description === undefined}>{description}</Text>
        </Stack>
      )}
    </UnstyledButton>
  );
};
