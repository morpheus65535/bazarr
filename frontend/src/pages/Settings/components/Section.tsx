import { Divider, Stack, Title } from "@mantine/core";
import { FunctionComponent } from "react";

interface SectionProps {
  header: string;
  hidden?: boolean;
}

export const Section: FunctionComponent<SectionProps> = ({
  header,
  hidden,
  children,
}) => {
  return (
    <Stack hidden={hidden} spacing="xs" my="lg">
      <Title order={4}>{header}</Title>
      <Divider></Divider>
      {children}
    </Stack>
  );
};
