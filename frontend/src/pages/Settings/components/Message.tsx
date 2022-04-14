import { Text } from "@mantine/core";
import { FunctionComponent } from "react";

export const Message: FunctionComponent<{
  type?: "warning" | "info";
}> = ({ type = "info", children }) => {
  return (
    <Text size="sm" color={type === "info" ? "dimmed" : "yellow"} mb="xs">
      {children}
    </Text>
  );
};
