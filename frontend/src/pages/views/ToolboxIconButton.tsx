import { ComponentProps } from "react";
import { Button, ButtonProps } from "@mantine/core";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

// Toolbar button with the icon stacked above its label.
export const ToolboxIconButton = ({
  icon,
  children,
  ...props
}: { icon: IconDefinition } & ButtonProps &
  Omit<ComponentProps<"button">, "ref">) => (
  <Button
    variant="subtle"
    color="gray"
    size="xs"
    leftSection={<FontAwesomeIcon icon={icon} size="lg" />}
    styles={{
      root: { height: "auto", padding: "6px 12px" },
      inner: { flexDirection: "column", gap: 6 },
      section: { marginInlineEnd: 0 },
    }}
    {...props}
  >
    {children}
  </Button>
);

export default ToolboxIconButton;
