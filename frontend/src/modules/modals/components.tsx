import { Container, Divider } from "@mantine/core";
import { FunctionComponent, ReactNode } from "react";

interface StandardModalProps {
  title: string;
  footer?: ReactNode;
}

export const StandardModalView: FunctionComponent<StandardModalProps> = ({
  children,
  footer,
  title,
}) => {
  return (
    <Container px={0}>
      {children}
      {footer && <Divider my="md"></Divider>}
      {footer}
    </Container>
  );
};
