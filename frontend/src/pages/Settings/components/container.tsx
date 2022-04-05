import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Card as MantineCard,
  Col,
  Divider,
  Group as MantineGroup,
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
    <MantineGroup hidden={hidden}>
      {name && <Text>{name}</Text>}
      {children}
    </MantineGroup>
  );
};

interface CardProps {
  header?: string;
  subheader?: string;
  plus?: boolean;
  onClick?: () => void;
}

export const ColCard: FunctionComponent<CardProps> = (props) => {
  return (
    <Col className="p-2" xs={6} lg={4}>
      <Card {...props}></Card>
    </Col>
  );
};

export const Card: FunctionComponent<CardProps> = ({
  header,
  subheader,
  plus,
  onClick,
}) => {
  return (
    <MantineCard className="settings-card" onClick={() => onClick && onClick()}>
      {plus ? (
        <MantineCard.Section>
          <FontAwesomeIcon size="2x" icon={faPlus}></FontAwesomeIcon>
        </MantineCard.Section>
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
