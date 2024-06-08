import { FunctionComponent, PropsWithChildren } from "react";
import { Text } from "@mantine/core";

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
