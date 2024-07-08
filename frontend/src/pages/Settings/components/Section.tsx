import { FunctionComponent, PropsWithChildren } from "react";
import { Divider, Stack, Title } from "@mantine/core";

interface SectionProps {
  header: string;
  hidden?: boolean;
}

type Props = PropsWithChildren<SectionProps>;

export const Section: FunctionComponent<Props> = ({
  header,
  hidden,
  children,
}) => {
  return (
    <Stack hidden={hidden} gap="xs" my="lg">
      <Title order={4}>{header}</Title>
      <Divider></Divider>
      {children}
    </Stack>
  );
};
