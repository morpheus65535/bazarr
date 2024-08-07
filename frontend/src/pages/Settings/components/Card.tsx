import { FunctionComponent } from "react";
import {
  Center,
  MantineStyleProp,
  Stack,
  Text,
  UnstyledButton,
} from "@mantine/core";
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
  titleStyles?: MantineStyleProp | undefined;
}

export const Card: FunctionComponent<CardProps> = ({
  header,
  description,
  plus,
  onClick,
  lineClamp,
  titleStyles,
}) => {
  return (
    <UnstyledButton p="lg" onClick={onClick} className={styles.card}>
      {plus ? (
        <Center>
          <FontAwesomeIcon size="2x" icon={faPlus}></FontAwesomeIcon>
        </Center>
      ) : (
        <Stack h="100%" gap={0}>
          <Text fw="bold" style={titleStyles}>
            {header}
          </Text>
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
