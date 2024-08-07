import { FunctionComponent } from "react";
import { Center, Stack, Text, UnstyledButton } from "@mantine/core";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import TextPopover from "@/components/TextPopover";
import styles from "./Card.module.scss";

interface CardProps {
  description?: string;
  header?: string;
  lineClamp?: number | undefined;
  onClick?: () => void;
  plus?: boolean;
}

export const Card: FunctionComponent<CardProps> = ({
  header,
  description,
  plus,
  onClick,
  lineClamp,
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
          <TextPopover text={description}>
            <Text hidden={description === undefined} lineClamp={lineClamp}>
              {description}
            </Text>
          </TextPopover>
        </Stack>
      )}
    </UnstyledButton>
  );
};
