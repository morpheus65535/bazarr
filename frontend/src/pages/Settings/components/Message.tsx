import { Text } from "@mantine/core";
import { FunctionComponent, PropsWithChildren } from "react";

interface MessageProps {
  type?: "warning" | "info";
}

type Props = PropsWithChildren<MessageProps>;

export const Message: FunctionComponent<Props> = ({
  type = "info",
  children,
}) => {
  return (
    <Text size="sm" c={type === "info" ? "dimmed" : "yellow"} my={0}>
      {children}
    </Text>
  );
};
